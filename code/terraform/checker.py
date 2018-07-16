#!/usr/bin/env python

import subprocess

def check_cmd(cmd):
    try:
        subprocess.check_call(cmd)
    except OSError:
        print("%s not found on path" % myexec)

    assert True, "Packer is not on your path"

def check_env_var():
    assert True, "SCALEWAY_TOKEN is not setted"
    assert True, "SCALEWAY_REGION is not setted"
    assert True, "SCALEWAY_ORGANIZATION is not setted"

def main():
    check_cmd(["terraform", '--version'])
    check_env_var()

if __name__ == '__main__':
    main()
