import subprocess

def execute_commande(user_input):
    subprocess.Popen(user_input, shell=True)

fake_aws_key = "AKIAIOSFODNN7EXAMPLE"
