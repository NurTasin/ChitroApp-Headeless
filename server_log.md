# ChitroAI LOGS

## 2023-03-08 12:52:43.582940
### Image Generation Error
```
Exception:     InvalidRequestError
Message:       Your request was rejected as a result of our safety system. Your prompt may contain text that is not allowed by our safety system.
Prompt:        Chicken fry eating a man
Mapped Prompt: Chicken fry eating a man
Chitro ID:     10d6fcc3-3b72-480e-aae1-57a594254a7b
IP Address:    127.0.0.1
Traceback: 
Traceback (most recent call last):
  File "app.py", line 121, in generate_image_thread
    response = openai.Image.create(prompt=translated_prompt,
  File "/home/bigt/.local/lib/python3.8/site-packages/openai/api_resources/image.py", line 36, in create
    response, _, api_key = requestor.request(
  File "/home/bigt/.local/lib/python3.8/site-packages/openai/api_requestor.py", line 227, in request
    resp, got_stream = self._interpret_response(result, stream)
  File "/home/bigt/.local/lib/python3.8/site-packages/openai/api_requestor.py", line 620, in _interpret_response
    self._interpret_response_line(
  File "/home/bigt/.local/lib/python3.8/site-packages/openai/api_requestor.py", line 680, in _interpret_response_line
    raise self.handle_error_response(
openai.error.InvalidRequestError: Your request was rejected as a result of our safety system. Your prompt may contain text that is not allowed by our safety system.

```

