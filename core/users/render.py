from rest_framework.renderers import JSONRenderer


class BaseResponse(object):
    def __init__(self):
        self.code = "0000"
        self.message = '请求成功'
        self.advice = ''
        self.data = None

    @property
    def dict(self):
        return self.__dict__


class FitJSONRenderer(JSONRenderer):

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response_body = BaseResponse()
        response = renderer_context.get("response")
        if response.status_code >= 400:
            response_body.data = None
            response_body.message = str(data)
        else:
            response_body.data = data
        renderer_context.get("response").status_code = 200
        return super(FitJSONRenderer, self).render(response_body.dict, accepted_media_type, renderer_context)