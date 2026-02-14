from appinfo import templates

def get_html_message_response(request, message_type, title, message, status_code):
    """
    Return a template response for an error page with the given message and status code.
    :param request: Request object
    :param message_type: 'success', 'error'
    :param title: str
    :param message: str
    :param status_code: str
    :return: TemplateResponse
    """
    return templates.TemplateResponse(
        request,
        "message.html",
        {
            "message_type": message_type,
            "status_code": status_code,
            "title": title,
            "message": message,
        },
        status_code=status_code,
    )
