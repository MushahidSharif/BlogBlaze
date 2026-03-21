import uvicorn

if __name__ == "__main__":
    #uvicorn.run("main:app", reload=True, host="0.0.0.0", port=8000)
    uvicorn.run("main:app", reload=True, host="0.0.0.0", port=8000, proxy_headers=True, forwarded_allow_ips="*")
    #uvicorn.run("main:app", reload=False, host="0.0.0.0", port=8000, workers=3, proxy_headers=True, forwarded_allow_ips="*")


