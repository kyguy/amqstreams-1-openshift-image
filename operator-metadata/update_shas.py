#!/usr/bin/env python
'''########################################################
 FILE: update_shas.py
 DESC: Updates CSV file to use the latest SHA digests
 
 EXEC: ./update_shas.py
########################################################'''
import yaml
import koji as brew
import sys
import os
import re

BREW_URL="http://brewhub.devel.redhat.com/brewhub"

PRODUCT_VERSION="1.5.0"

# TODO: Use operator to get current version and version of other components from brew
NVR_PREFIX = {
  "strimzi-cluster-operator" : "amqstreams-operator-container",
  "strimzi-kafka-24"         : "amqstreams-kafka-24",
  "strimzi-kafka-25"         : "amqstreams-kafka-25",
  "strimzi-bridge"           : "amqstreams-bridge"
}

# Clone, update, commit


def get_csv_file():
  path = "./manifests"
  for filename in os.listdir(path):
    if re.match("(.)*.clusterserviceversion.yaml", filename):
      csv_file = os.path.join(path, filename)
      return csv_file

def extract_micro(s):
  s = re.sub(r'amqstreams-bundle-container-', '', s)
  return re.sub(r'-.*', '', s)


def get_csv_version(brew_client, prefix, f):
  ''' Takes and returns csv version number'''
  with open("example.yaml", 'r') as stream:
    try:
        print(yaml.safe_load(stream))
    except yaml.YAMLError as exc:
        print(exc)


  # Query brew
  print(PRODUCT_VERSION[0:-2])
  for build in brew_client.listBuilds(prefix=prefix):
    if(build['version'][0:-2] == PRODUCT_VERSION[0:-2]):
      # Process to get latest micro
      print(extract_micro(build['nvr']))
      
  #match = re.search('(\d.\d.\d)', f)
  #if match:
  #  return match.group(1)

def get_nvr(brew_client, prefix, version):
    ''' Gets nvr of latest brew build with the specified prefix e.g. amqstreams-operator-container-1.4.0-5'''
    for build in brew_client.listBuilds(prefix=prefix):
      if(build['version'] == version):
          return build['nvr']
    raise ValueError('No NVR found in brew with prefix %s and version %s' % (prefix, version))

def get_sha(brew_client, nvr):
  try:
    # Get Manifest List Digest associated with nvr
    #sha = brew_client.getBuild(nvr)['extra']['image']['index']['digests']['application/vnd.docker.distribution.manifest.list.v2+json']

    # Get Image Digest associated with nvr
    print(nvr)
    sha = brew_client.listArchives(brew_client.getBuild(nvr)['build_id'])[0]['extra']['docker']['digests']['application/vnd.docker.distribution.manifest.v2+json']
    print('NVR: %s %s' % (nvr, sha))
  except:
    print("No NVR found in brew with value", nvr)

  return sha

def format_sha(s):
  return s.split(":")[-1]

def create_sha_dict(brew_client, csv_file, version):
  with open(csv_file, 'r') as stream:
    try:
      CSV=yaml.safe_load(stream)
      sha_dict = {}
      print("--- Retrieving SHAs for most recent NVRs ---")
      for entry in CSV["spec"]["relatedImages"]:
        name  = entry['name']
        image = entry['image']

        nvr_prefix = NVR_PREFIX.get(name)
        print(nvr_prefix)
        old_sha = format_sha(image)
        new_sha = format_sha(get_sha(brew_client, get_nvr(brew_client, nvr_prefix, version)))

        sha_dict[old_sha] = new_sha

      return sha_dict
    except yaml.YAMLError as exc:
      print(exc)

def update_csv_file(csv_file, sha_dict):
  with open(csv_file, 'r') as file :
    filedata = file.read()

  print("-- Updating CSV with SHAs from most recent NVRs--")
  for old_sha, new_sha in sha_dict.items():
    print("Replacing " + old_sha + " with " + new_sha)
    filedata = filedata.replace(old_sha, new_sha)

  with open(csv_file, 'w') as file:
    file.write(filedata)

def increment_micro_version(s):
  tmp = s.split(".")
  
  tmp[-1] = str(int(tmp[-1]) + 1)
  return ".".join(tmp)

def increment_csv_version(csv_file, csv_version):   
  new_version = increment_micro_version(csv_version)
  
  with open(csv_file, "r") as sources:
    lines = sources.read()
  with open(csv_file, "w") as sources:
    lines = lines.replace(version, new_version)
    sources.write(re.sub(r'replaces: amqstreams.v.*..*..*', 'replaces: amqstreams.v' + version, lines))

def main():
  print("===== EXECUTING RENDER_TEMPLATES ======")
  brew_client = brew.ClientSession(BREW_URL)

  csv_file    = get_csv_file()
  csv_version = get_csv_version(brew_client, "amqstreams-bundle-container", csv_file)

  #increment_csv_version(csv_file, csv_version)
  #sha_dict = create_sha_dict(brew_client, csv_file, PRODUCT_VERSION)
  #update_csv_file(csv_file, sha_dict)

if __name__ == "__main__":
    main()

