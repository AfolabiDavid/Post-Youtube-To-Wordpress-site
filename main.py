import requests
from datetime import datetime, timedelta
import creds

# This app fetches the latest youtube videos from a Youtube Playlist.

print(f'\u2713 Process initiated')

api_key = creds.api_key

# playlist_id = input(f'Enter Playlist ID: ')
#
# if not playlist_id:
#
# else:
#     playlist_id = playlist_id

playlist_id = creds.playlist_id
def get_youtube_videos(api_key, playlist_id):
    base_url = "https://www.googleapis.com/youtube/v3"

    # Get playlist items
    playlist_url = f"{base_url}/playlistItems"
    playlist_params = {
        'part': 'snippet,contentDetails',  # Corrected 'part' parameter
        'playlistId': playlist_id,
        'key': api_key,
        'maxResults': 1,  # Adjust as needed
        'order': 'date'
    }

    response = requests.get(playlist_url, params=playlist_params)
    data = response.json()

    return data

response = get_youtube_videos(api_key, playlist_id)


for item in response['items']:
    snippet = item['snippet']
    yt_videoPublishedAt = snippet.get("publishedAt")
    title = snippet.get("title")
    video_id = snippet.get("resourceId").get("videoId")
    thumbnail_standard_url = snippet.get("thumbnails").get("standard").get("url")
    embed_url = f"https://www.youtube.com/embed/{video_id}"

    # Check if there is actual Recording date to set the videoPublished date, otherwise reset date to Sunday or Wed
    title_date_str = title.split()[-1]



    try:
        yt_videoPublishedAt = datetime.strptime(title_date_str, "%d-%m-%Y").date()
        date_check = f'There is Date in Title. Date is: {yt_videoPublishedAt.strftime("%A")} and the day is No: {yt_videoPublishedAt.isoweekday()}'
    except ValueError:
        # If there is no date in title
        yt_videoPublishedAt = item.get("contentDetails").get("videoPublishedAt")
        yt_videoPublishedAt = datetime.strptime(yt_videoPublishedAt[:10], "%Y-%m-%d").date()
        date_check = f'No Date in Title. UPLOAD DAY is {yt_videoPublishedAt.strftime("%A")}, {yt_videoPublishedAt} and the day is No: {yt_videoPublishedAt.isoweekday()}'

        sub_days = yt_videoPublishedAt.isoweekday()
        startofweek = yt_videoPublishedAt - timedelta(days=sub_days)

        # def startofweek(yt_videoPublishedAt):
        #     sub_days = yt_videoPublishedAt.isoweekday()
        #     start_week = yt_videoPublishedAt - timedelta(days=sub_days)
        #     return start_week

        if yt_videoPublishedAt.isoweekday() < 3:
            # if yt_videoPublishedAt.isoweekday() != 7 and yt_videoPublishedAt.isoweekday() < 3:
            yt_videoPublishedAt = startofweek
            date_check = f'No Date in Title. UPLOAD DAY has been reset to = {yt_videoPublishedAt} which is = {yt_videoPublishedAt.strftime("%A")} and the day is No: {yt_videoPublishedAt.isoweekday()}'

        elif yt_videoPublishedAt.isoweekday() != 7 and yt_videoPublishedAt.isoweekday() > 3:
            yt_videoPublishedAt = startofweek + timedelta(days=3)
            date_used = f'No Date in Title. UPLOAD DAY has been reset to = {yt_videoPublishedAt} which is = {yt_videoPublishedAt.strftime("%A")} and the day is No: {yt_videoPublishedAt.isoweekday()}'

        elif yt_videoPublishedAt.isoweekday() == 7:
            yt_videoPublishedAt = startofweek
            date_check = f'No Date in Title. UPLOAD DAY has been reset to = {yt_videoPublishedAt} which is = {yt_videoPublishedAt.strftime("%A")} and the day is No: {yt_videoPublishedAt.isoweekday()}'

        else:
            yt_videoPublishedAt = startofweek + timedelta(days=3)
            date_check = f'No Date in Title. UPLOAD DAY has been reset to = {yt_videoPublishedAt} which is = {yt_videoPublishedAt.strftime("%A")} and the day is No: {yt_videoPublishedAt.isoweekday()}'

        print(f' \u2713 Date set and adjusted as follows: {date_check}')



    # Upload Image and return the image id and the image title
    # =========================================================================

    from wordpress_xmlrpc import Client, WordPressPost
    from wordpress_xmlrpc.compat import xmlrpc_client
    from wordpress_xmlrpc.methods import media
    from wordpress_xmlrpc.methods import posts

    # from wordpress_xmlrpc.exceptions import ProtocolError
    xmlrpc_endpoint = 'https://dev.gharvestisland.org/xmlrpc.php'
    username = creds.username
    password = creds.password

    # Initialize WordPress XML-RPC client
    wp = Client(xmlrpc_endpoint, username, password)

    def upload_image_to_wp(thumbnail_standard_url):
        # Download image from the web
        upload_image = requests.get(thumbnail_standard_url)

        if upload_image.status_code == 200:
            # Upload the image to the WordPress media library using media module
            data = {
                'name': f'{title}.jpg',
                'type': 'image/jpg',
                'bits': xmlrpc_client.Binary(upload_image.content),
                'overwrite': True,
            }

            img_id = wp.call(media.UploadFile(data))
            # img_title = m.get("title").get("rendered");

            # Print the uploaded image's attachment ID

            # print(f"Image uploaded successfully! Attachment ID: {img_id}")

            return img_id
        else:
            # print(f"Failed to download image. HTTP Status Code: {upload_image.status_code}")
            return None

    # Upload image to WordPress
    img_upload = upload_image_to_wp(thumbnail_standard_url)

    if img_upload is not None:
        img_id = img_upload.get("attachment_id")
        print(f"\u2713 Image uploaded successfully! Image ID is : {img_id}")

    else:
        img_id = ''
        print(f"Image upload was not successful! ")

    # Set/initialize Sermon Post parameters
    post_mp = {"title": title, "date": f"{yt_videoPublishedAt} 09:00:00", "postformat_video_embed": embed_url,
               "featured_media": img_id, "status": "publish", "author": 9, "template": "", "content": embed_url,
               "type": "sermons", "comment_status": "closed", "ping_status": "closed", "format": "video"}

    # print(f'{video_id} | {title} | {yt_videoPublishedAt} {embed_url} {thumbnail_standard_url}')

    # ============ Post sermon to Wordpress using the Post Param  =========
    import xmlrpc.client
    import time
    import signal


    # Function to create a sermon post
    def create_sermon_post(title, embed_url, img_id, yt_videoPublishedAt):
        try:
            # Your WordPress XML-RPC request
            post = WordPressPost()
            post.title = title
            post.post_status = 'publish'
            post.author = 9
            # post.content = 'embed_url'
            post.post_type = 'sermons'
            post.comment_status = 'closed'
            post.ping_status = 'closed'
            post.post_format = 'video'
            post.custom_fields = [{'key': 'postformat_video_embed', 'value': embed_url}]
            post.thumbnail = img_id
            yt_date_str = yt_videoPublishedAt.strftime('%Y-%m-%d')
            yt_date = datetime.strptime(yt_date_str, '%Y-%m-%d')
            # Set post_date field explicitly without leading zeros
            post.date = datetime(yt_date.year, yt_date.month, yt_date.day)

            # Upload the post
            post_id = wp.call(posts.NewPost(post))
            post_url = wp.call(posts.GetPost(post_id)).link

            print(f'\u2713 Sermon post created successfully! Post ID: {post_id} {post_url}')

            # sermon_check = f"Sermon post created successfully! Post ID & URL: {post_id} {post_url}"

            return post_id, post_url

        except xmlrpc.client.Fault as e:
            if "429" in str(e):  # Check if the error is a 429 error
                print("Rate limit exceeded. Retrying after a delay.")
                time.sleep(10)  # Adjust the delay as needed
                # Retry the request
                return create_sermon_post(title, embed_url, img_id, yt_videoPublishedAt)
            else:
                # Handle other XML-RPC faults
                print(f"XML-RPC Fault: {e}")
                return None

    # Signal handler for handling SIGINT
    def signal_handler(signal, frame):
        print("SIGINT received. Exiting gracefully.")
        # You can add cleanup code here if needed
        exit(0)

    # Register the signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Call the function to create the sermon post
    result = create_sermon_post(title, embed_url, img_id, yt_videoPublishedAt)

    # Check if the result is not None before unpacking
    if result:
        post_id, post_url = result
        # Print the post ID and URL
        print(f'{post_mp}')
        print(f'\u2713 Sermon posting process completed. Post ID: {post_id} Post URL: {post_url} POST PARAM {date_check}')

    else:
        print("Error creating the sermon post.")