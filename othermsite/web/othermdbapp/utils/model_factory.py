# used to get model class from string
from django.apps import apps
from django.db import models
from django.db.models.fields import AutoField

# a class to create models and populate their fields dynamically
class ModelFactory:
    # parameter is a list of dicts:
    #   the key is the name of the model (ex: "Site")
    #   the value is another dict where `key=>val` is `field=>value`
    #   if the field is a ForeignKey, the "value" is *another* dictionary,
    #     specifying enough fields to narrow down one model instance 
    #   (see comment at bottom)
    #
    # - returns the names of the saved models in a dictionary
    # - raises exceptions for any parsing/logistic errors 
    def create_models(model_list, save=True):
        saved_models = []
        exceptions = []
        for model_i in model_list:
            for model_name, fields in model_i.items():
                try:
                    # create object
                    model = ModelFactory.__get_model_object(model_name)
                    # populate fields
                    ModelFactory.__populate_fields(model, fields)
                    # save the model
                    if save:
                        model.save()
                        field_list = [f"{f.name}:  {getattr(model, f.name)}"  
                            for f in model._meta.fields if not isinstance(f, AutoField)]
                        saved_models.append({"model": model, "fields": field_list, "type":model_name})
                except Exception as e:
                    exceptions.append(e)
        return (saved_models, exceptions)

    # get the initial model object from a string
    def __get_model_object(model_string):
        try:
            model_class = apps.get_model(
                app_label='othermdbapp', model_name=model_string)
            return model_class()
        except Exception as error:
            e = f"Cannot find class from string \"{model_string}\": {error}"
            raise ModelFactoryException(e) from error
    
    # populates the fields of a model
    def __populate_fields(model, field_dict):
        # loop through the fields
        for field, value in field_dict.items():    
            # makes sure the field is legit
            try:
                # checks if field is a foreignkey
                if isinstance(model._meta.get_field(field), models.ForeignKey):
                    # get the model target of the key
                    fk_class = model._meta.get_field(field).remote_field.model
                    # value is our dictionary of field:value for the targeted instances
                    kwargs = {f"{f}__exact":v for (f,v) in value.items() }
                    # find all matching targets
                    qs = fk_class.objects.filter(**kwargs)
                    # if we don't have exactly one match, throw error
                    if qs.count() != 1:
                        e = f"Found {qs.count()} {fk_class.__name__} matches using criteria: {value}"
                        raise ModelFactoryException(e)
                    # otherwise, set the field accordingly
                    setattr(model, field, qs.first())
                else:
                    setattr(model, field, value)
            except Exception as error:
                e1 = f"Cannot set field \"{field}\""
                e2 = f"{e1} of model \"{model._meta.model_name}\": {error}"
                raise ModelFactoryException(e2) from error
        # validate the model
        try:
            model.full_clean()
        except Exception as error:
            e = f"Error validating model {model._meta.model_name}: {error}"
            raise ModelFactoryException(e) from error

class ModelFactoryException(Exception):
    pass

# ------------------------
# example dictionary below
# ------------------------

# "Manufacturer" =>
#     "name" => "Example Manufacturer",
#     "description" => "This is just an example manufacturer",
#     "equipment_type" => 
#         "name" => "This is the name of the eq. type we want to reference"

# ------------------------
# example dictionary above
# ------------------------

# Notes:
#  - equipment_type is a ForeignKey, so it necessitates specifying more fields
#       * this can be done as shown below, using a field like "name"
#       * if there are multiple EquipmentType objects with the same "name",
#            an exception will be thrown
#       * "pk" can also be specified, which will be the primary key/id of
#           the object. this will ensure only one object matches