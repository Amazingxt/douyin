import os

def run():
    if not os.path.exists('./myprojectenv'):
        os.system('virtualenv myprojectenv')
    else:
        pass

if __name__ == "__main__":
    run()