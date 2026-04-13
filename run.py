import uvicorn

def main():
    uvicorn.run("src.main:app", host="0.0.0.0", port=3780)

if __name__ == "__main__":
    main()
