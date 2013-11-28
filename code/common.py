import os
import web
from mako import exceptions
from web.contrib.template import render_mako

template_directory = os.path.join(os.path.dirname(__file__), '../templates')

def mako_debug(func):
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return exceptions.html_error_template().render()
    return wrapped

class debug_render_mako:
    def __init__(self, *a, **kwargs):
        from mako.lookup import TemplateLookup
        self._lookup = TemplateLookup(*a, **kwargs)

    def __getattr__(self, name):
        # Assuming all templates are html
        path = name + ".html"
        t = self._lookup.get_template(path)

        def wrapped(*args, **kwargs):
            try:
                return t.render(*args, **kwargs)
            except:
                return exceptions.html_error_template().render()
        
        return wrapped

if web.config.debug == True:
    render = debug_render_mako(
        directories=[template_directory],
        input_encoding='utf-8',
        output_encoding='utf-8')
else:
    render = render_mako(
        directories=[template_directory],
        input_encoding='utf-8',
        output_encoding='utf-8')    

        

