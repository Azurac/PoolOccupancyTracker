import uvicorn

def main():
    uvicorn.run("src.main:app", port=8000)

if __name__ == "__main__":
    main()