import argparse
import flickrapi

helpstring = 'usage: instagram-stsearch.py -h(elp) -t <access-token> -b <bbox min-lon,max-lon,min-lat,max-lat> -s <start timestamp in human readable format> -e <end timestamp in human readable format> -o <outputfile> [-r <radius of search circles, default 5000m>]'

argparser = argparse.ArgumentParser()
argparser.add_argument("api_key", help="instagram access-token", type=str)
argparser.add_argument("lon_min", help="bounding box minimum longitude", type=float)
argparser.add_argument("lon_max", help="bounding box maximum longitude", type=float)
argparser.add_argument("lat_min", help="bounding box minimum latitude", type=float)
argparser.add_argument("lat_max", help="bounding box maximum latitude", type=float)
argparser.add_argument("output", help="output location", type=str)
args = argparser.parse_args()	

flickr = flickrapi.FlickrAPI(args.api_key, cache=True)
bbox_string = str(args.lon_min) + ',' + str(args.lat_min) + ',' + str(args.lon_max) + ',' + str(args.lat_max)
i = 1
f = open(args.output, "a")
while True:
	print "page", i
	photos = flickr.photos_search(bbox=bbox_string, page=str(i))
	if len(photos[0]) == 0:
		break
	j = 1
	for photo in photos[0]:
		print "photo", j
		photoLoc = flickr.photos_geo_getLocation(photo_id=photo.attrib['id'])
		photoInfo = flickr.photos_getInfo(photo_id=photo.attrib['id'])
		photoTags = flickr.tags_getListPhoto(photo_id=photo.attrib['id']).find('photo').find('tags')
		tags = []
		for tag in photoTags.getiterator():
			if not (tag.get('raw') is None):
				tags.append(tag.get('raw'))
		f.write(photo.attrib['id'] + ';' + photo.attrib['title'].encode('utf-8') + ';' + photo.attrib['owner'] + ';' + photoLoc[0][0].attrib['longitude'] + ';' + photoLoc[0][0].attrib['latitude'] + ';' + photoInfo.find('photo').find('dates').get('taken') + ';' + ','.join(tags).encode('utf-8') + '\n')
		j = j + 1
	i = i + 1
f.close()