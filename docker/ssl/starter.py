import os

domain = "your-domain"

def set_domain(domain):
    for dname, dirs, files in os.walk(os.getcwd()):
        for fname in files:
            fpath = os.path.join(dname, fname)
            with open(fpath) as f:
                s = f.read()
            s = s.replace("localhost", domain)
            with open(fpath, "w") as f:
                f.write(s)
                print("%s updated" %fname )


if __name__ == "__main__":
    set_domain(domain)

