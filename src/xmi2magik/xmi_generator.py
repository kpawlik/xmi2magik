# -*- coding: UTF-8 -*-
#!/usr/bin/python

from collections import namedtuple #@UnresolvedImport
from getpass import getuser
from datetime import datetime
from string import Template
import os


###############################################
## Module functions
###############################################
"""
Workaround for python version 3.0 to 3.2.
"""
def callable(object):
    return hasattr(object, "__call__")


###############################################
## Class
###############################################
class MagikGenMixin(object):
    """
    Class contains mixin functionality for generate 
    Magik source.
    """
    pragma_template = "_pragma(classify_level={{{0}}}, topic={{{1}}})"
    
    def gen_class_crt(self):
        """
        Return class of namedtuple
        """
        self.gen_class = namedtuple("Meta", self.gen_class_fields())
        

    def gen_class_fields_values(self):
        """
        Return list of values calculated from self.fields 
        """
        fields_val = []
        fields_val_append = fields_val.append
        for field in self.fields:
            if callable(field):
                fields_val_append(field())
            else:
                fields_val_append(getattr(self, field))
        return fields_val
    
    
    def crt_gen_class(self):
        """
        Return instance of namedtuple
        """
        fields_val = self.gen_class_fields_values()
        return self.gen_class._make(fields_val)

    
    def gen_class_fields(self):
        """
        Retunr string. List of fields names to crate 
        class of namedtuple
        """
        lof = []
        lof_append = lof.append
        for field in self.fields:
            if callable(field):
                lof_append(field.__name__)
            else:
                lof_append(field)
        
        return " ".join(lof)

 
    def generate(self):
        """
        format template based on namedtuple
        """
        self.gen_class_crt()
        m = self.crt_gen_class()
        return self.template.format(meta=m)   


    def generate_pragma(self):
        """
        Generate pragma stmt depend on 
        visibility and topic
        """
        level = self.get_level()
        topic = self.get_topic()
        return self.pragma_template.format(level, topic) 
    

    def get_level(self):
        """
        return pragma level
        """
        vis = "basic"
        if self.visibility == "private":
            vis = "restricted"
        return vis
    

    def get_topic(self):
        return self.topic

    
    def __str__(self):
        return self.name

    
    def to_string(self, topic=""):
        self.topic = topic
        res_strings = list()
        res_strings.append(self.generate_pragma())
        res_strings.append(self.generate())
        return "\n".join(res_strings)
     

###############################################
## Class
###############################################
class UmlObject(object):
    """
    Base class for all other Magik elements
    """
    
    #------------------------------------------    
    def __init__(self, id, name, visibility="public"):
        self.visibility = visibility
        self.id = id
        self.name = name
        
###############################################
## Class
###############################################
class Model(UmlObject):
    """
    Base class for all other Magik elements
    """
    
    #------------------------------------------    
    def __init__(self, *args):
        self.classes = []
        self.packages = []
        super(Model, self).__init__(*args)        
  
    def model_classes(self):
        pckg_classes = set()
        for pckg in self.packages:
            pckg_classes.update(pckg.classes)
        
        self_classes = set(self.classes)
        self_classes.intersection(pckg_classes)
        return self_classes
   
###############################################
## Class
###############################################
class Exemplar(MagikGenMixin, UmlObject):
    """
    class which will generate exemplar
    """
    template = """def_slotted_exemplar(:{meta.name},
    ## 
    {{
{meta.g_attributes}
    }},
    {{ {meta.g_ancestors} }})
$
"""

    def __init__(self, *args):
        self.operations = []
        self.attributes = []
        self.ancestors = []
        self.fields = ( "name",
                        self.g_attributes, 
                        self.g_ancestors )
        
        super(Exemplar, self).__init__(*args)        

    
    def g_ancestors(self):
        """
        Return list of ancestors joined with semicolon
        """
        ancest = map(lambda a: ":{0}".format(a), self.ancestors)
        return ", ".join(ancest)
   
   
    def g_attributes(self):
        """
        Return list of attributes
        """
        res = []
        res_append = res.append
        for attr in self.attributes:
            res_append("\t{{:{0}, _unset}}".format(attr))
        return ",\n".join(res)
    
    
    def to_string(self, topic=""):
        str = super(Exemplar, self).to_string(topic)
        res_strings = list()
        res_string_append = res_strings.append
        res_string_append(str)
        for attr in self.attributes:
            res_string_append(attr.to_string(topic))
        for op in self.operations:
            res_string_append(op.to_string(topic))
                
        return "\n".join(res_strings)
                
        
    
    
###############################################
## Class
###############################################
class Package(UmlObject):
    """
    class which will generate module
    """
    
   
    def __init__(self, *args):
        self.classes = []
        self.fields = ()
        super(Package, self).__init__(*args)
        
    

###############################################
## Class
###############################################
class Operation(MagikGenMixin, UmlObject):
    """
    class which will generate method body
    """
    template="""{meta.g_visibility}{meta.g_abstract}_method {meta.exemplar}.{meta.name}({meta.g_in_parameters})
\t##
\t## 
{meta.g_parameters_comment}
\t##
{meta.g_body}
_endmethod
$    
"""
    
    def __init__(self, *args):
        self.exemplar = "exemaplar"
        self.visibility = "public"
        self.abstract = False
        self.parameters = []
        self.fields = ("exemplar",
                       "name",
                       self.g_abstract,
                       self.g_in_parameters,
                       self.g_parameters_comment,
                       self.g_visibility,
                       self.g_body)
         
        super(Operation, self).__init__(*args)
        
    
    def g_abstract(self):
        if self.abstract:
            return "_abstract "
        else:
            return ""  

    
    def g_in_parameters(self):
        """
        generate in parameters
        """
        pp = [p for p in self.parameters if p.direction in ("IN", "INOUT")]
        if pp:
            return ", ".join([str(p) for p in pp])
        else:
            return ""
        
        
    def g_out_parameters(self):
        """
        generate declaration of out params
        """
        params = [p for p in self.parameters if p.direction in ("OUT")]
        t = "\t_local {0} << _unset"
        res = [t.format(p) for p in params]
        if res:
            return "\n".join(res)
        else:
            return ""
        
    
    def g_inout_parameters(self):
        """
        generate return statement with out and inout params 
        """
        params = [str(p) for p in self.parameters if p.direction in ("OUT", "INOUT")]
        if params:
            return "\t_return ({0})".format(", ".join(params))
        else:
            return ""
    
    
    def g_body(self):
        """
        Generate method body
        """
        res = []
        res_append = res.append
        outp = self.g_out_parameters()
        if outp:
            res_append(outp)
        inoutp = self.g_inout_parameters()
        if inoutp:
            res_append(inoutp)
        return "\n".join(res)
    

    def g_parameters_comment(self):
        """
        Generate list of parameters for comment
        """
        res = []
        res_append = res.append
        for param in self.parameters:
            res_append("\t## {0}".format(param))
        
        return "\n".join(res)
    

    def g_visibility(self):
        """
        Return visibility statement for method
        """
        if self.visibility != "public":
            return "_private "
        else:
            return ""


###############################################
## Class
###############################################
class Parameter(MagikGenMixin,UmlObject):
    """
    Operation parameter
    """
    def __init__(self, *args):
        self.direction = "IN"
        super(Parameter, self).__init__(*args)
        

###############################################
## Class
###############################################
class Attribute(MagikGenMixin, UmlObject):
    """
    Exemplar attribute
    """
    template = """{meta.exemplar}.define_slotted_access(:{meta.name}, :{meta.g_accesibility}, :{meta.visibility})
$
"""
    def __init__(self, *args):
        self.exemplar = "exemplar"
        self.visibility = "public"
        self.fields = ( "exemplar",
                        "name",
                        "visibility", 
                        self.g_accesibility )

        super(Attribute, self).__init__(*args)
    
    
    def g_accesibility(self):
        return "writable"


###############################################
## Class
###############################################
class FilesGenerator(object):
    """
    """
    def __init__(self, object_list, target_folder, topic, header, package, encoding):
        self.target_folder = target_folder
        self.uml_objects = object_list
        self.topic = topic
        self.header = self._header(header)
        self.package = package
        self.encoding = encoding
        
        
    def _header(self, header):
        user = getuser()
        date = datetime.now().strftime("%d.%m.%Y")
        theader = Template(header)
        return theader.safe_substitute({"user":user, 
                                        "date":date})
        
    
    def generate(self):
        for model in self.uml_objects:
            self.generate_classes(model.model_classes())
            for pckg in model.packages:
                self.generate_classes(pckg.classes)
    
    
    def generate_classes(self, classes):
        for cls in classes:
            path = os.path.join(self.target_folder, "{0}.magik".format(cls.name))
            data = []
            data.append("% text_encoding = {0}\n_package {1}\n$".format(self.encoding,
                                                                        self.package))
            data.append(self.header)
            data.append(cls.to_string(self.topic))
            out = open(path, "w")
            try:
                out.write("\n\n".join(data))
            finally:
                out.close()
                
    
    
    