

def send_output(stdout, text, path):
    if stdout:
        print(text)
    else:
        try:
            fp = open(path, 'a', encoding='utf-8')
            fp.write(text)
            fp.close()
        except Exception as e:
            print(f"I/O Exception: unable to write to {path}")
            print(e)
            exit(1)