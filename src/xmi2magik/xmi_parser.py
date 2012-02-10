# -*- coding: UTF-8 -*-
#!/usr/bin/python

from xml.dom.minidom import parse
from xmi_generator import Attribute, Exemplar, Operation, Package, Parameter, Model


###############################################
## Module functions
###############################################


def filter_by_attr(iter, *args, **kwargs):
    """
    filter iterable element 
    by args - check if element from iter has attributes named attrs
    by kwargs - check if element has attribute with value
    Example:
        filter_by_attr(list, "name")
          will return all elements with attribute name if this attr
          exists.
        filter_by_attr(list, "name", age="12")
          will return all elements with attribute name if this attr
          exists and attr age eq "12"
    """
    func = None
    if args:
        func = filter_by_attr_name(*args)
        iter = filter(func, iter)
    if kwargs:
        func = filter_by_attr_val(**kwargs)
        iter = filter(func, iter)
    return iter


def filter_by_attr_name(*args):
    """
    return function to filter 
    """
    def filter(obj):
        obj_attr_get = obj.attributes.get
        for k in args:
            if not obj_attr_get(k):
                return False
        return True 
    return filter
            
def filter_by_attr_val(**kwargs):
    """
    return function to filter
    """
    def filter(obj):
        for k,v in kwargs.items():
            if obj.getAttribute(k)!= v:
                return False
        return True 
    return filter

def query_elements(xml, tag_name, *args, **kwargs ):
    elements = xml.getElementsByTagName(tag_name)
    return filter_by_attr(elements, *args, **kwargs)
        
def named_elements(xml, tag_name, attribute="name"):
    all = xml.getElementsByTagName(tag_name)
    return filter_by_attr(all, attribute)

def xmi_parent_node(obj):
    obj.parentNode.parentNode.nodeName


###############################################
## Class
###############################################
class XmiParser(object):
    """
    XMI parser class. Parse dom object to UmlObjects
    """
    # Class attributes and methods
    tag_name = ""
    parsers = dict()
    
    uml_classes = {"UML:Model" : Model,
                   "UML:Class" : Exemplar,
                   "UML:Package" : Package,
                   "UML:Attribute": Attribute,
                   "UML:Parameter" : Parameter,
                   "UML:Operation" : Operation}
    
    @classmethod
    def register_parser(cls, parser, tag=None):
        """
        Register parser class with key in parsers dict
        """
        if not tag:
            tag = parser.tag_name
        cls.parsers[tag] = parser
    
    
    
    @classmethod
    def parser(cls, type, dom):
        """
        Return appropriate parser for type
        """
        parser_class = cls.parsers.get(type)
        if parser_class:
            return parser_class(dom)
    
    @classmethod
    def parse_file(self, path):
        dom = parse(path)
        parser = self.parser("UML:Model", dom)
        obj = parser.parse()
        parser.parse_generalization()
        return obj


    # Instance methods
    def __init__(self, xml):
        self.xml = xml
        # to set generalization
        self.parsed_obj = dict()
        self.objects = named_elements(xml, self.tag_name)
   
        
    def _id_name(self, obj):
        """
        Return attributes id, name from obj
        """
        name = obj.getAttribute("name")
        id = obj.getAttribute("xmi.id")
        return id, name
    

    def _visibility(self, obj):
        """
        Return visibility attribute of obj
        """
        res = "public"
        vis = obj.getAttribute("visibility")
        if vis in ("private", "protected"):
                res = "private"
        return res 
    
    
    def _crt_new(self, obj, cls):
        """
        Create new instance of cls with attributes id and name
        """
        id, name = self._id_name(obj)
        return cls(id, name), id

    
    def parse(self, parent_name=None):
        """
        parse objects with self.tag_name
        """
        objects = list()
        objects_append = objects.append
        obj_class = self.uml_classes.get(self.tag_name)
        for obj in self.objects:
            new, id = self._crt_new(obj, obj_class)
            objects_append(new)
            self.parsed_obj[id]=new
            self.parse_obj(obj, new)
        
        return objects
    
    
    def parse_obj(self, model, new):
        """
        parse children
        """
        for child, attr in self.children.items():
            parser = self.parser(child, model)
            children = parser.parse()
            setattr(new, attr, children) 
            self.parsed_obj.update(parser.parsed_obj)
    

    def parse_generalization(self):
        """
        """
        generalizations = named_elements(self.xml, "UML:Generalization")
        for general in generalizations:
            child_id = general.getAttribute("child")    
            parent_id = general.getAttribute("parent")
            child = self.parsed_obj[child_id]
            parent = self.parsed_obj[parent_id]
            child.ancestors.append(parent)
    
###############################################
## Class
###############################################
class ModelParser(XmiParser):
    """
    """
    
    children = {"UML:Package" : "packages",
                "UML:Class" : "classes"}
    tag_name = "UML:Model"
    
        

XmiParser.register_parser(ModelParser)
 
###############################################
## Class
###############################################
class PackageParser(XmiParser):
    """
    """
    
    children = {"UML:Class" : "classes"}
    tag_name = "UML:Package"
            
XmiParser.register_parser(PackageParser)

###############################################
## Class
###############################################
class ClassParser(XmiParser):
    """
    """
    
    children = {"UML:Operation" : "operations",
                "UML:Attribute" : "attributes"}
    tag_name = "UML:Class"
            
XmiParser.register_parser(ClassParser)


###############################################
## Class
###############################################
class AttributeParser(XmiParser):
    """
    """
    
    children = {}
    tag_name = "UML:Attribute"
    
    def _crt_new(self, obj, cls):
        new, id = super(AttributeParser, self)._crt_new(obj, cls)
        new.visibility = self._visibility(obj)
        
        return new, id

XmiParser.register_parser(AttributeParser)

###############################################
## Class
###############################################
class OperationParser(XmiParser):
    """
    """
    
    children = {"UML:Parameter": "parameters"}
    tag_name = "UML:Operation"
    
    def _crt_new(self, obj, cls):
        new, id = super(OperationParser, self)._crt_new(obj, cls)
        new.visibility = self._visibility(obj)
        
        return new, id

XmiParser.register_parser(OperationParser)


###############################################
## Class
###############################################
class ParameterParser(XmiParser):
    """
    """
    
    children = {}
    tag_name = "UML:Parameter"
    
    def _crt_new(self, obj, cls):
        new, id = super(ParameterParser, self)._crt_new(obj, cls)
        dir = obj.getAttribute("kind")
        if dir in ("out", "return"):
            new.direction = "OUT"
        else:
            new.direction = dir.upper()
        
        return new, id
        
XmiParser.register_parser(ParameterParser)

