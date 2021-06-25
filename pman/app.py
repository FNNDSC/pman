
import os

from flask import Flask
from flask_restful import Api

from .config import DevConfig, ProdConfig
from pman.resources import JobListResource, JobResource


def create_app(config_dict=None):
    app_mode = os.environ.get("APPLICATION_MODE", default="production")
    if app_mode == 'production':
        config_obj = ProdConfig()
    else:
        config_obj = DevConfig()

    app = Flask(__name__)
    app.config.from_object(config_obj)
    app.config.update(config_dict or {})

    api = Api(app, prefix='/api/v1/')

    # url mappings
    api.add_resource(JobListResource, '/', endpoint='api.joblist')
    api.add_resource(JobResource, '/<string:job_id>/', endpoint='api.job')

    return app
