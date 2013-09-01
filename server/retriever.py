import requests
from pprint import pprint
import os
import json
from PIL import Image 
from os import path
import time

IMAGE_DIR_RAW = path.join(path.dirname(__file__), 'images_raw')
IMAGE_DIR_PROCESSED = path.join(path.dirname(__file__), 'images_processed')

def getLatestUrl():
	response = requests.get('http://mars.jpl.nasa.gov/msl-raw-images/image/image_manifest.json')
	data = response.json()

	latest_sol = data['sols'][-1]
	sol_url = latest_sol['catalog_url']
	return sol_url
	
	
	
def getLatestImages(image_count):
	
	response = requests.get(getLatestUrl())
	data = response.json()
	
	images = data['images']
	#Filter
	print 'raw length: ', len(images)
	filtered = []
	for i in images:
		if 'NAV_' in i['instrument'] and i["sampleType"] == "full":
			filtered.append(i)
			
	filtered = filtered[-image_count:]
	print 'filtered length: ', len(filtered)
	if len(filtered) == 0:
		print 'warning, filtered image len == 0.  Adding all images back in'
		filtered = images[-image_count:]
		print 'new filtered len: ', len(filtered)

	metadata = []
	for i in filtered:
		metadata.append({'instrument' : i['instrument'],
			'url' : i['urlList'],
			'utc' : i['utc'],
			'id' : i['itemName'],
			'site' : i['site'],
			'sol' : i['sol']
			})
	return metadata
	
def saveRawImages(images):
	# Remove old images
	print 'removing old images'
	for name in os.listdir(IMAGE_DIR_RAW):
		os.remove(path.join(IMAGE_DIR_RAW, name))
	for i in images:
		i['filename'] = i['id'] + '.jpg'
		outFile = open(path.join(IMAGE_DIR_RAW, i['filename']), 'w')
		request = requests.get(i['url'], stream=True)
		for block in request.iter_content(1024):
			if not block:
				break
		 	outFile.write(block)
		outFile.close()
		print 'saving: ', i['id'], '.png'
	outManifest = open(path.join(IMAGE_DIR_RAW, 'manifest.json'), 'w')
	outManifest.write(json.dumps(images))
	outManifest.close()
	#TODO: Save JSON manifest

def getImageData(filename):
	#Load
	img = Image.open(filename) # open colour image
	
	#Scale
	dims = (144,144)
	img.thumbnail(dims, Image.ANTIALIAS)
	
	#Black and white
	img = img.convert('1') # convert image to black and white

	#Save Temp
	img.save(path.join(IMAGE_DIR_PROCESSED, filename.split('/')[-1].split('.')[0] + ".png"))

	# Convert to bytestream
	bytes = []
	for i in range(img.size[1]):
		for j in range(img.size[0]):
			bytes.append(int(bool(img.getpixel((i,j)))))
	return bytes

def processImages():
	image_files = os.listdir(IMAGE_DIR_RAW)
	f = open(path.join(IMAGE_DIR_RAW, 'manifest.json'), 'r')
	manifest = json.loads(f.read())
	f.close()

	response = []
	for obj in manifest:
		data = getImageData(path.join(IMAGE_DIR_RAW, obj['filename']))
		data_bytes = []
		data_str = [str(d) for d in data]
		for i in range(len(data)/8):
			num = int(''.join(data_str[8*i:8*(i+1)]), 2)
			#data_bytes.append(num)
			#### 
			# REVERSE BYTES
			nums = bin(num)[2:]
			nums = '0' * (8-len(nums)) + nums
			nums = nums[::-1]
			data_bytes.append(int(nums,2))
			####
			
		secs = time.mktime(time.localtime()) - time.mktime(time.strptime("2013-08-30T15:07:12Z", "%Y-%m-%dT%H:%M:%SZ"))
		hours = int(secs/3600)
		if hours == 0:
			title = str(int(secs/61)) + ' mins '
		else:
			title = str(hours) + ' hours '
		title += 'ago from ' + obj['instrument']
		response.append({
			#'data' : data,
      'data_bytes' : data_bytes,
      'width' : 144,
      'height' : 144,
			'title' : title,
			'filename' : obj['filename'].replace('jpg', 'png'),
			'instrument' : obj['instrument'],
			'utc' : obj['utc'],
			'site': obj['site'],
			'sol': obj['sol']
		})
	print 'Writing output file...'
	f = open(path.join(IMAGE_DIR_PROCESSED, 'manifest.json'), 'w')
	f.write(json.dumps(response))
	f.close()
	return response

def main(image_count):
	images = getLatestImages(image_count)
	pprint(images)
	saveRawImages(images)
	data = processImages()
	
	
if __name__ == '__main__':
	main(5)
	
	
	
	


