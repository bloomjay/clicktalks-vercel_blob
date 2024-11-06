from fastapi import FastAPI , HTTPException, Depends,File,UploadFile,Path,Query,Form
from pydantic import BaseModel,EmailStr
from fastapi.middleware.cors import CORSMiddleware
import httpx
import vercel_blob
from typing import List
from uuid import UUID, uuid4
from fastapi.staticfiles import StaticFiles
import re,os
import aiomysql
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
from  email.message import EmailMessage
import logging
import psycopg2
import os
from urllib.parse import unquote

app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

os.environ['BLOB_READ_WRITE_TOKEN'] = 'vercel_blob_rw_WFcA5yW8LPNHoqpQ_vugq2K4G7cboT3E5nyvjNwlRtSCqjo'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailRequest(BaseModel):
    email: EmailStr


class Item(BaseModel):
    name: str
    email: str
    password: str
    city:str
    role:str
    phone:str

class MembershipData(BaseModel):
    address: str
    gender: str
    college: str
    referralsource: str
    reasontojoin: str
    interests: List[str]

class Post(BaseModel):
    path:str
    name:str

class UserDetails(BaseModel):
    role: str
    about_you: str
    clg: str
    achievements: str


class UserLogin(BaseModel):
    email: str
    password: str

class LikeUpdate(BaseModel):
    user_id: str
    image_path: str
    unique_id: str
    id:int

class UploadYoutube(BaseModel):
    unique_id:str
    youtube_path:str

class videotoyoutube(BaseModel):
    videoLink:str

class Voting(BaseModel):
    youtube_path:str
    name:str
    clg:str
    description:str

class LikeUpdate2(BaseModel):
    user_id: str
    video_path: str
    unique_id: str
    id:int

class LikeUpdate3(BaseModel):
    user_id: str
    youtube_path: str
    unique_id: str
    id:int


class Check_likes(BaseModel):
    image_path:str
    user_id:str
    unique_id:str


class Image(BaseModel):
    image_base64: str
    content_type: str

class Verify(BaseModel):
    email:str
    unique_id:str


class SearchData(BaseModel):
    search_text: str

class FollowRequest(BaseModel):
    user_id: str
    follower_id: str

class PasswordChange(BaseModel):
    email:EmailStr
    password:str



# conn_params = {
#     'host': "ep-broad-glade-a1buqdb7-pooler.ap-southeast-1.aws.neon.tech",
#     'user': "default",
#     'password': "6n3QqtgHvpWK",
#     'database': "verceldb",
# }
conn_params = {
    'host': "db.clicktalksnow.com",
    'user': "bloomtide",
    'password': "clicktalkstech@Hostinger1",
    'database': "bloomtide",
}
def get_db():
    conn = psycopg2.connect(**conn_params)
    try:
        yield conn
    finally:
        conn.close()

def uuid_to_table_name(uuid):
    return re.sub(r'[^a-zA-Z0-9]', '_', str(uuid))

# --------------------------------------------------------------------POST METHOD---------------------------------------------------------------------------------------------------
def send_otp_via_email(email: str, otp: str):
    sender_email = "clicktalkstech@gmail.com"
    sender_password = "ildb wojs cgih skst"
    receiver_email = email

    message = MIMEMultipart()
    message["Subject"] = "Your OTP Code"
    message["From"] = sender_email
    message["To"] = receiver_email

    text = f"Your OTP code is {otp}"
    part1 = MIMEText(text, "plain")
    
    message.attach(part1)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )
        

def read_file_content(file: UploadFile):
    return file.file.read()

@app.post("/send-otp/")
def send_otp(email_request: EmailRequest):
    otp = str(random.randint(100000, 999999))
    try:
        send_otp_via_email(email_request.email, otp)
        return {"otp": otp}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send email")
    




@app.post("/registration/", response_model=dict)
def create_item(item: Item, db=Depends(get_db)):
    # Automatically generate a unique ID for the student
    unique_id = uuid_to_table_name(uuid4())

    with db.cursor() as cur:
        # Check if the student's email is distinct from existing records
        cur.execute(
            "SELECT COUNT(*) FROM register_details WHERE email = %s",
            (item.email,)
        )
        count = cur.fetchone()
        if count[0] > 0:
            raise HTTPException(status_code=400, detail="Student with the same email already exists")

        # Insert the student details into the 'register' table
        cur.execute(
            "INSERT INTO register_details (unique_id, name, email, password,city,role,phone) VALUES (%s, %s, %s, %s,%s,%s,%s)",
            (str(unique_id), item.name, item.email, item.password,item.city,item.role,item.phone)
        )
        
        db.commit()



    # Return the created item
    return   {"unique_id": unique_id, "name": item.name, "email": item.email, "password": item.password}




@app.post("/upload_image/{unique_id}/{name}")
def upload_image(unique_id: str, name:str, file: UploadFile = File(...), db=Depends(get_db)):
    try:
        name=unquote(name)
        if not file:
            raise HTTPException(status_code=400, detail="No file uploaded")
        
        with db.cursor() as cur:

            # Check if the record with the provided unique_id exists in the database
            cur.execute("SELECT COUNT(*) FROM register_details WHERE unique_id = %s", (unique_id,))
            count = cur.fetchone()
            name=unquote(name)
            if count[0] == 0:
                raise HTTPException(status_code=404, detail="Record not found")
            
            file_content = read_file_content(file)
            resp = vercel_blob.put(file.filename, file_content)
            file_url = resp.get("url")

            # Insert the image path into the database
            cur.execute(
                "INSERT INTO images (unique_id, image_path, name) VALUES (%s, %s,%s)",
                (unique_id, file_url,name,)
            )
            db.commit()

        
        return {"message": "Image uploaded successfully"}
    except Exception as e:
        return {"error": str(e)} 










# @app.post("/upload_video/{unique_id}/{name}")
# def upload_video(unique_id: str, name:str, file: UploadFile = File(...), db=Depends(get_db)):
#     try:
#         if not file:
#             raise HTTPException(status_code=400, detail="No file uploaded")
        
#         with db.cursor() as cur:
#             # Check if the record with the provided unique_id exists in the database
#             cur.execute("SELECT COUNT(*) FROM register_details WHERE unique_id = %s", (unique_id,))
#             count = cur.fetchone()
#             if count[0] == 0:
#                 raise HTTPException(status_code=404, detail="Record not found")
            
#             # Save the uploaded video locally
#             file_content = read_file_content(file)
#             resp = vercel_blob.put(file.filename, file_content)
#             file_url = resp.get("url")

#             name=unquote(name)
           
            
#             # Insert the video path into the database
#             cur.execute(
#                 "INSERT INTO videos (unique_id, video_path, name) VALUES (%s, %s,%s)",
#                 (unique_id, file_url,name ,)
#             )
#             db.commit()
        
#         return {"message": "Video uploaded successfully"}
#     except Exception as e:
#         return {"error": str(e)}
    
@app.post('/upload_video/{unique_id}/{name}')
def upload_video(unique_id: str, name:str, items1:videotoyoutube , db=Depends(get_db)):
    with db.cursor() as cur:
        try:
            name=unquote(name)
            cur.execute("SELECT COUNT(*) FROM videos WHERE video_path = %s and unique_id=%s ", (items1.videoLink,unique_id,))
            count = cur.fetchone()
            if count[0] > 0:
                    return {"message": "video already exists"}


            cur.execute(
                "insert into videos (unique_id,video_path,name) values(%s,%s,%s)",(unique_id,items1.videoLink,name,)
            )
            db.commit()
            
            return {"message": " vedio uploaded successfully"}
        except Exception as e:
            return {"error": str(e)}
        

@app.post('/get_post/images')
def get_post_image(Items2:Post,db=Depends(get_db)):
      with db.cursor() as cur:
        try:
             cur.execute("SELECT * from images WHERE image_path = %s and name=%s ", (Items2.path,Items2.name,))
             images_data = cur.fetchall()
             image_paths = [{"id": row[0], "unique_id":row[1], "image_paths": row[2], "likes": row[3], "shares": row[4] ,"name":row[5]} for row in images_data]
            
             return {"image_paths": image_paths}
        except Exception as e:
             return {"error": str(e)}
        
@app.post('/get_post/video')
def get_post_image(Items2:Post,db=Depends(get_db)):
      with db.cursor() as cur:
        try:
             cur.execute("SELECT * from videos WHERE video_path = %s and name=%s ", (Items2.path,Items2.name,))
             images_data = cur.fetchall()
             image_paths = [{"id": row[0], "unique_id":row[1], "video_path": row[2], "likes": row[3], "shares": row[4] ,"name":row[5]} for row in images_data]
            
             return {"video_paths": image_paths}
        except Exception as e:
             return {"error": str(e)}

        

















@app.post("/verify_registration/")
def verify_registration(user: UserLogin,db=Depends(get_db)):
    email = user.email
    password = user.password
    with db.cursor() as cur:
        # Check if the provided email and password exist in the database
        cur.execute("SELECT unique_id, name FROM register_details WHERE email = %s and password = %s", (email, password,))
        student_data = cur.fetchone()
        if not student_data:
            raise HTTPException(status_code=404, detail="User not found")

        unique_id, name = student_data

    # If a matching record is found, return the student data
    return {"unique_id": unique_id, "email": email, "name": name}



@app.post("/verifyvotings/")
def verify_registration(user: Verify,db=Depends(get_db)):
    with db.cursor() as cur:
        # Check if the provided email and password exist in the database
        cur.execute("SELECT count(*) FROM verify WHERE email = %s and unique_id = %s", (user.email,user.unique_id ,))
        student_data = cur.fetchone()
        if student_data[0] > 0:
                return {"message": "email already voted"}
            


        cur.execute("insert into verify (unique_id,email) values(%s,%s)", (user.unique_id,user.email ,))
        db.commit()
    
    return {"result":"Sucessfully Voted"}


@app.post("/danceverifyvotings/")
def verify_registration(user: Verify,db=Depends(get_db)):
    with db.cursor() as cur:
        # Check if the provided email and password exist in the database
        cur.execute("SELECT count(*) FROM danceverify WHERE email = %s and unique_id = %s", (user.email,user.unique_id ,))
        student_data = cur.fetchone()
        if student_data[0] > 0:
                return {"message": "email already voted"}
            


        cur.execute("insert into danceverify (unique_id,email) values(%s,%s)", (user.unique_id,user.email ,))
        db.commit()
    
    return {"result":"Sucessfully Voted"}



@app.post("/photoverifyvotings/")
def verify_registration(user: Verify,db=Depends(get_db)):
    with db.cursor() as cur:
        # Check if the provided email and password exist in the database
        cur.execute("SELECT count(*) FROM photoverify WHERE email = %s and unique_id = %s", (user.email,user.unique_id ,))
        student_data = cur.fetchone()
        if student_data[0] > 0:
                return {"message": "email already voted"}
            


        cur.execute("insert into photoverify (unique_id,email) values(%s,%s)", (user.unique_id,user.email ,))
        db.commit()
    
    return {"result":"Sucessfully Voted"}



@app.post("/fashionverifyvotings/")
def verify_registration(user: Verify,db=Depends(get_db)):
    with db.cursor() as cur:
        # Check if the provided email and password exist in the database
        cur.execute("SELECT count(*) FROM fashionverify WHERE email = %s and unique_id = %s", (user.email,user.unique_id ,))
        student_data = cur.fetchone()
        if student_data[0] > 0:
                return {"message": "email already voted"}
            


        cur.execute("insert into fashionverify (unique_id,email) values(%s,%s)", (user.unique_id,user.email ,))
        db.commit()
    
    return {"result":"Sucessfully Voted"}

@app.post("/standupverifyvotings/")
def verify_registration(user: Verify,db=Depends(get_db)):
    with db.cursor() as cur:
        # Check if the provided email and password exist in the database
        cur.execute("SELECT count(*) FROM standupverify WHERE email = %s and unique_id = %s", (user.email,user.unique_id ,))
        student_data = cur.fetchone()
        if student_data[0] > 0:
                return {"message": "email already voted"}
            


        cur.execute("insert into standupverify (unique_id,email) values(%s,%s)", (user.unique_id,user.email ,))
        db.commit()
    
    return {"result":"Sucessfully Voted"}

@app.post("/singingverifyvotings/")
def verify_registration(user: Verify,db=Depends(get_db)):
    with db.cursor() as cur:
        # Check if the provided email and password exist in the database
        cur.execute("SELECT count(*) FROM singingverify WHERE email = %s and unique_id = %s", (user.email,user.unique_id ,))
        student_data = cur.fetchone()
        if student_data[0] > 0:
                return {"message": "email already voted"}
            


        cur.execute("insert into singingverify (unique_id,email) values(%s,%s)", (user.unique_id,user.email ,))
        db.commit()
    
    return {"result":"Sucessfully Voted"}

@app.post("/actingverifyvotings/")
def verify_registration(user: Verify,db=Depends(get_db)):
    with db.cursor() as cur:
        # Check if the provided email and password exist in the database
        cur.execute("SELECT count(*) FROM actingverify WHERE email = %s and unique_id = %s", (user.email,user.unique_id ,))
        student_data = cur.fetchone()
        if student_data[0] > 0:
                return {"message": "email already voted"}
            


        cur.execute("insert into actingverify (unique_id,email) values(%s,%s)", (user.unique_id,user.email ,))
        db.commit()
    
    return {"result":"Sucessfully Voted"}










@app.post("/search_bar/")
def search_users(search_data: SearchData, db=Depends(get_db)):
    search_text = f"%{search_data.search_text}%"
    with db.cursor() as cur:
       
        cur.execute("SELECT name FROM register_details WHERE name LIKE (%s)",(search_text,))
        student_data = cur.fetchall()
        names = [row[0] for row in student_data]
    return {"Names":names}



@app.post("/follow", response_model=dict)
def follow(follow_request: FollowRequest, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO followers (user_id, follower_id) VALUES (%s, %s)",
            (follow_request.user_id, follow_request.follower_id,)
        )
        db.commit()
    return {"message": "Followed successfully"}


@app.post('/upload/youtube_video/{name}')
def upload_youtube(list_items:UploadYoutube,name:str, db=Depends(get_db)):
    with db.cursor() as cur:
        try:
            name=unquote(name)
            cur.execute("SELECT COUNT(*) FROM youtube_videos WHERE youtube_path = %s and unique_id=%s ", (list_items.youtube_path,list_items.unique_id,))
            count = cur.fetchone()
            if count[0] > 0:
                    return {"message": "youtube_vedio already exists"}


            cur.execute(
                "insert into youtube_videos (unique_id,youtube_path,name) values(%s,%s,%s)",(list_items.unique_id,list_items.youtube_path,name,)
            )
            db.commit()
            
            return {"message": "youtube vedio successfully"}
        except Exception as e:
            return {"error": str(e)}
        


@app.post("/upload_voting_videos/", response_model=dict)
def create_item(item: Voting, db=Depends(get_db)):
    # Automatically generate a unique ID for the student
    unique_id = uuid_to_table_name(uuid4())
    

    with db.cursor() as cur:
        # Check if the student's name and email are distinct from existing records
        cur.execute(
            "SELECT COUNT(*) FROM votingvedios  WHERE name = %s ",
            (item.name,)
        )
        count = cur.fetchone()
        if count[0] > 0:
            raise HTTPException(status_code=400, detail="Student with the same name or email already exists")

        # Insert the student details into the 'register' table
        cur.execute(
            "INSERT INTO votingvedios (user_id, name, youtube_path,likes,clg,description) VALUES (%s, %s,%s,%s,%s,%s)",
            (str(unique_id), item.name,item.youtube_path,0,item.clg,item.description)
        )
        
        db.commit()


    return  {"result":"uploaded sucessfully"}


@app.post("/upload_Dance_voting_videos/", response_model=dict)
def create_item(item: Voting, db=Depends(get_db)):
    # Automatically generate a unique ID for the student
    unique_id = uuid_to_table_name(uuid4())
    

    with db.cursor() as cur:
        # Check if the student's name and email are distinct from existing records
        cur.execute(
            "SELECT COUNT(*) FROM dancevotingvideos  WHERE name = %s ",
            (item.name,)
        )
        count = cur.fetchone()
        if count[0] > 0:
            raise HTTPException(status_code=400, detail="Student with the same name or email already exists")

        # Insert the student details into the 'register' table
        cur.execute(
            "INSERT INTO dancevotingvideos (user_id, name, youtube_path,likes,clg,description) VALUES (%s, %s,%s,%s,%s,%s)",
            (str(unique_id), item.name,item.youtube_path,0,item.clg,item.description)
        )
        # cur.execute(
        #     "INSERT INTO dancevotingvideos (user_id, name, youtube_path,likes) VALUES (%s, %s,%s,%s)",
        #     (str(unique_id), item.name,item.youtube_path,0,)
        # )
        
        db.commit()


    return  {"result":"uploaded sucessfully"}



@app.post("/upload_photo_voting_videos/", response_model=dict)
def create_item(item: Voting, db=Depends(get_db)):
    # Automatically generate a unique ID for the student
    unique_id = uuid_to_table_name(uuid4())
    

    with db.cursor() as cur:
        # Check if the student's name and email are distinct from existing records
        cur.execute(
            "SELECT COUNT(*) FROM photovotingvideos  WHERE name = %s ",
            (item.name,)
        )
        count = cur.fetchone()
        if count[0] > 0:
            raise HTTPException(status_code=400, detail="Student with the same name or email already exists")

        # Insert the student details into the 'register' table
        cur.execute(
            "INSERT INTO photovotingvideos (user_id, name, youtube_path,likes,clg,description) VALUES (%s, %s,%s,%s,%s,%s)",
            (str(unique_id), item.name,item.youtube_path,0,item.clg,item.description)
        )
        # cur.execute(
        #     "INSERT INTO photovotingvideos (user_id, name, youtube_path,likes) VALUES (%s, %s,%s,%s)",
        #     (str(unique_id), item.name,item.youtube_path,0,)
        # )
        
        db.commit()


    return  {"result":"uploaded sucessfully"}



@app.post("/upload_fashion_voting_videos/", response_model=dict)
def create_item(item: Voting, db=Depends(get_db)):
    # Automatically generate a unique ID for the student
    unique_id = uuid_to_table_name(uuid4())
    

    with db.cursor() as cur:
        # Check if the student's name and email are distinct from existing records
        cur.execute(
            "SELECT COUNT(*) FROM fashionvotingvideos  WHERE name = %s ",
            (item.name,)
        )
        count = cur.fetchone()
        if count[0] > 0:
            raise HTTPException(status_code=400, detail="Student with the same name or email already exists")

        # Insert the student details into the 'register' table
        cur.execute(
            "INSERT INTO fashionvotingvideos (user_id, name, youtube_path,likes,clg,description) VALUES (%s, %s,%s,%s,%s,%s)",
            (str(unique_id), item.name,item.youtube_path,0,item.clg,item.description)
        )
        # cur.execute(
        #     "INSERT INTO fashionvotingvideos (user_id, name, youtube_path,likes) VALUES (%s, %s,%s,%s)",
        #     (str(unique_id), item.name,item.youtube_path,0,)
        # )
        
        db.commit()


    return  {"result":"uploaded sucessfully"}

@app.post("/upload_standup_voting_videos/", response_model=dict)
def create_item(item: Voting, db=Depends(get_db)):
    # Automatically generate a unique ID for the student
    unique_id = uuid_to_table_name(uuid4())
    

    with db.cursor() as cur:
        # Check if the student's name and email are distinct from existing records
        cur.execute(
            "SELECT COUNT(*) FROM standupvotingvideos  WHERE name = %s ",
            (item.name,)
        )
        count = cur.fetchone()
        if count[0] > 0:
            raise HTTPException(status_code=400, detail="Student with the same name or email already exists")

        # Insert the student details into the 'register' table
        cur.execute(
            "INSERT INTO standupvotingvideos (user_id, name, youtube_path,likes,clg,description) VALUES (%s, %s,%s,%s,%s,%s)",
            (str(unique_id), item.name,item.youtube_path,0,item.clg,item.description)
        )
        # cur.execute(
        #     "INSERT INTO standupvotingvideos (user_id, name, youtube_path,likes) VALUES (%s, %s,%s,%s)",
        #     (str(unique_id), item.name,item.youtube_path,0,)
        # )
        
        db.commit()


    return  {"result":"uploaded sucessfully"}

@app.post("/upload_singing_voting_videos/", response_model=dict)
def create_item(item: Voting, db=Depends(get_db)):
    # Automatically generate a unique ID for the student
    unique_id = uuid_to_table_name(uuid4())
    

    with db.cursor() as cur:
        # Check if the student's name and email are distinct from existing records
        cur.execute(
            "SELECT COUNT(*) FROM singingvotingvideos  WHERE name = %s ",
            (item.name,)
        )
        count = cur.fetchone()
        if count[0] > 0:
            raise HTTPException(status_code=400, detail="Student with the same name or email already exists")

        # Insert the student details into the 'register' table
        cur.execute(
            "INSERT INTO singingvotingvideos (user_id, name, youtube_path,likes,clg,description) VALUES (%s, %s,%s,%s,%s,%s)",
            (str(unique_id), item.name,item.youtube_path,0,item.clg,item.description)
        )
        # cur.execute(
        #     "INSERT INTO singingvotingvideos (user_id, name, youtube_path,likes) VALUES (%s, %s,%s,%s)",
        #     (str(unique_id), item.name,item.youtube_path,0,)
        # )
        
        db.commit()


    return  {"result":"uploaded sucessfully"}

@app.post("/upload_acting_voting_videos/", response_model=dict)
def create_item(item: Voting, db=Depends(get_db)):
    # Automatically generate a unique ID for the student
    unique_id = uuid_to_table_name(uuid4())
    

    with db.cursor() as cur:
        # Check if the student's name and email are distinct from existing records
        cur.execute(
            "SELECT COUNT(*) FROM actingvotingvideos  WHERE name = %s ",
            (item.name,)
        )
        count = cur.fetchone()
        if count[0] > 0:
            raise HTTPException(status_code=400, detail="Student with the same name or email already exists")

        # Insert the student details into the 'register' table
        cur.execute(
            "INSERT INTO actingvotingvideos (user_id, name, youtube_path,likes,clg,description) VALUES (%s, %s,%s,%s,%s,%s)",
            (str(unique_id), item.name,item.youtube_path,0,item.clg,item.description)
        )
        # cur.execute(
        #     "INSERT INTO actingvotingvideos (user_id, name, youtube_path,likes) VALUES (%s, %s,%s,%s)",
        #     (str(unique_id), item.name,item.youtube_path,0,)
        # )
        
        db.commit()


    return  {"result":"uploaded sucessfully"}


@app.post("/upload_user_details_card/{unique_id}",response_model=dict)
def upload_user_details(unique_id: str, db=Depends(get_db)):
    with db.cursor() as cur:
        profile_image_path='https://wfca5yw8lpnhoqpq.public.blob.vercel-storage.com/blob-qnvdlbgAyYFi3NviN7FZ36fM8i2u2F'
        cover_image_path='https://wfca5yw8lpnhoqpq.public.blob.vercel-storage.com/blob-FWGZ8Jim2mftnk6LMHWvFGQ40pj8fR'
        cur.execute(
            "INSERT INTO details (unique_id, name ,profile_image,cover_image, about_you, studies,achievements) VALUES (%s, %s,%s,%s,%s,%s,%s)",
            (unique_id,'photography',profile_image_path,cover_image_path,"welcome to click talks now ",'NIT warangal','gold medalist',)
        )
        
        db.commit()


    return  {"result":"uploaded sucessfully"}











       
    







# Endpoint for retrieving image paths from MySQL





# --------------------------------------------------------------------------GET METHOD ---------------------------------------------------------------
@app.get("/images/{unique_id}/")
def get_images(unique_id: str, db=Depends(get_db)):
    try:
        with db.cursor() as cur:
            # Retrieve image paths from the database based on the unique_id
            cur.execute("SELECT * FROM images WHERE unique_id = %s", (unique_id,))
            images_data = cur.fetchall()
            image_paths = [{"id": row[0], "unique_id":row[1], "image_paths": row[2], "likes": row[3], "shares": row[4] ,"name":row[5]} for row in images_data]
            
        return {"image_paths": image_paths}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/get_emails/")
def get_emails(db=Depends(get_db)):
    try:
         with db.cursor() as cur:
            cur.execute("SELECT email FROM register_details")
            emails_data = cur.fetchall()
            emails = [row[0] for row in emails_data]
            
         return {"emails": emails}
    except Exception as e:
        return {"error": str(e)}

    
@app.get("/get_voting_videos/")
def get_images( db=Depends(get_db)):
    try:
        with db.cursor() as cur:
            # Retrieve image paths from the database based on the unique_id
            cur.execute("SELECT * FROM votingvedios ")
            images_data = cur.fetchall()
            image_paths = [{"id": row[0], "name":row[1],"unique_id":row[2], "youtube_path": row[3], "likes": row[4],"clg":row[5],'descrpt':row[6]} for row in images_data]
            
        return {"result": image_paths}
    except Exception as e:
        return {"error": str(e)}
    

@app.get("/get_short_film_video_by_id/{id}")
def get_images(id:str,db=Depends(get_db)):
    try:
        with db.cursor() as cur:
            # Retrieve image paths from the database based on the unique_id
            cur.execute("SELECT * FROM votingvedios where id= %s",(id,))
            images_data = cur.fetchall()
            image_paths = [{"id": row[0], "name":row[1],"unique_id":row[2], "youtube_path": row[3], "likes": row[4],"clg":row[5],'descrpt':row[6]} for row in images_data]
            
        return {"result": image_paths}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/get_dance_video_by_id/{id}")
def get_images(id:str,db=Depends(get_db)):
    try:
        with db.cursor() as cur:
            # Retrieve image paths from the database based on the unique_id
            cur.execute("SELECT * FROM dancevotingvideos where id= %s",(id,))
            images_data = cur.fetchall()
            image_paths = [{"id": row[0], "name":row[1],"unique_id":row[2], "youtube_path": row[3], "likes": row[4],"clg":row[5],'descrpt':row[6]} for row in images_data]
            
        return {"result": image_paths}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/get_fashion_video_by_id/{id}")
def get_images(id:str,db=Depends(get_db)):
    try:
        with db.cursor() as cur:
            # Retrieve image paths from the database based on the unique_id
            cur.execute("SELECT * FROM fashionvotingvideos where id= %s",(id,))
            images_data = cur.fetchall()
            image_paths = [{"id": row[0], "name":row[1],"unique_id":row[2], "youtube_path": row[3], "likes": row[4],"clg":row[5],'descrpt':row[6]} for row in images_data]
            
        return {"result": image_paths}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/get_standup_video_by_id/{id}")
def get_images(id:str,db=Depends(get_db)):
    try:
        with db.cursor() as cur:
            # Retrieve image paths from the database based on the unique_id
            cur.execute("SELECT * FROM standupvotingvideos where id= %s",(id,))
            images_data = cur.fetchall()
            image_paths = [{"id": row[0], "name":row[1],"unique_id":row[2], "youtube_path": row[3], "likes": row[4],"clg":row[5],'descrpt':row[6]} for row in images_data]
            
        return {"result": image_paths}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/get_singing_video_by_id/{id}")
def get_images(id:str,db=Depends(get_db)):
    try:
        with db.cursor() as cur:
            # Retrieve image paths from the database based on the unique_id
            cur.execute("SELECT * FROM singingvotingvideos where id= %s",(id,))
            images_data = cur.fetchall()
            image_paths = [{"id": row[0], "name":row[1],"unique_id":row[2], "youtube_path": row[3], "likes": row[4],"clg":row[5],'descrpt':row[6]} for row in images_data]
            
        return {"result": image_paths}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/get_acting_video_by_id/{id}")
def get_images(id:str,db=Depends(get_db)):
    try:
        with db.cursor() as cur:
            # Retrieve image paths from the database based on the unique_id
            cur.execute("SELECT * FROM actingvotingvideos where id= %s",(id,))
            images_data = cur.fetchall()
            image_paths = [{"id": row[0], "name":row[1],"unique_id":row[2], "youtube_path": row[3], "likes": row[4],"clg":row[5],'descrpt':row[6]} for row in images_data]
            
        return {"result": image_paths}
    except Exception as e:
        return {"error": str(e)}
    

@app.get("/get_photographer_video_by_id/{id}")
def get_images(id:str,db=Depends(get_db)):
    try:
        with db.cursor() as cur:
            # Retrieve image paths from the database based on the unique_id
            cur.execute("SELECT * FROM photovotingvideos where id= %s",(id,))
            images_data = cur.fetchall()
            image_paths = [{"id": row[0], "name":row[1],"unique_id":row[2], "youtube_path": row[3], "likes": row[4],"clg":row[5],'descrpt':row[6]} for row in images_data]
            
        return {"result": image_paths}
    except Exception as e:
        return {"error": str(e)}
    

@app.get("/get_dance_voting_videos/")
def get_images(db=Depends(get_db)):
    try:
        with db.cursor() as cur:
            # Retrieve image paths from the database based on the unique_id
            cur.execute("SELECT * FROM dancevotingvideos ")
            images_data = cur.fetchall()
            image_paths = [{"id": row[0], "name":row[1],"unique_id":row[2], "youtube_path": row[3], "likes": row[4],"clg":row[5],'descrpt':row[6]} for row in images_data]
            
        return {"result": image_paths}
    except Exception as e:
        return {"error": str(e)}


@app.get("/get_photo_voting_videos/")
def get_images( db=Depends(get_db)):
    try:
        with db.cursor() as cur:
            # Retrieve image paths from the database based on the unique_id
            cur.execute("SELECT * FROM photovotingvideos ")
            images_data = cur.fetchall()
            image_paths = [{"id": row[0], "name":row[1],"unique_id":row[2], "youtube_path": row[3], "likes": row[4],"clg":row[5],'descrpt':row[6]} for row in images_data]
            
        return {"result": image_paths}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/get_fashion_voting_videos/")
def get_images( db=Depends(get_db)):
    try:
        with db.cursor() as cur:
            # Retrieve image paths from the database based on the unique_id
            cur.execute("SELECT * FROM fashionvotingvideos ")
            images_data = cur.fetchall()
            image_paths = [{"id": row[0], "name":row[1],"unique_id":row[2], "youtube_path": row[3], "likes": row[4],"clg":row[5],'descrpt':row[6]} for row in images_data]
            
        return {"result": image_paths}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/get_standup_voting_videos/")
def get_images( db=Depends(get_db)):
    try:
        with db.cursor() as cur:
            # Retrieve image paths from the database based on the unique_id
            cur.execute("SELECT * FROM standupvotingvideos ")
            images_data = cur.fetchall()
            image_paths = [{"id": row[0], "name":row[1],"unique_id":row[2], "youtube_path": row[3], "likes": row[4],"clg":row[5],'descrpt':row[6]} for row in images_data]
            
        return {"result": image_paths}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/get_singing_voting_videos/")
def get_images( db=Depends(get_db)):
    try:
        with db.cursor() as cur:
            # Retrieve image paths from the database based on the unique_id
            cur.execute("SELECT * FROM singingvotingvideos ")
            images_data = cur.fetchall()
            image_paths = [{"id": row[0], "name":row[1],"unique_id":row[2], "youtube_path": row[3], "likes": row[4],"clg":row[5],'descrpt':row[6]} for row in images_data]
            
        return {"result": image_paths}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/get_acting_voting_videos/")
def get_images( db=Depends(get_db)):
    try:
        with db.cursor() as cur:
            # Retrieve image paths from the database based on the unique_id
            cur.execute("SELECT * FROM actingvotingvideos ")
            images_data = cur.fetchall()
            image_paths = [{"id": row[0], "name":row[1],"unique_id":row[2], "youtube_path": row[3], "likes": row[4],"clg":row[5],'descrpt':row[6]} for row in images_data]
            
        return {"result": image_paths}
    except Exception as e:
        return {"error": str(e)}
    
    


    
@app.get("/get_youtube_video/{unique_id}")
def get_youtube_video(unique_id:str, db=Depends(get_db)):
        with db.cursor() as cur:
            cur.execute("SELECT * FROM youtube_videos WHERE unique_id = %s", (unique_id,))
            display_data=cur.fetchall()
            result=[{"id": row[0], "unique_id":row[1], "youtube_path": row[2], "likes": row[3],"name":row[4]} for row in display_data]

        return {"result":result}


@app.get("/videos/{unique_id}/")
def get_videos(unique_id: str, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT *  FROM videos where unique_id=(%s)",(unique_id,))
        videos = cur.fetchall()
        # Convert the fetched data into a list of dictionaries
        videos_data = [{"id": row[0], "unique_id":row[1], "video_path": row[2], "likes": row[3], "shares": row[4],"name":row[5]} for row in videos]
        return {"videos": videos_data}
    


@app.get("/followers_count/{unique_id}")
def get_followers_count(unique_id: str, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM followers WHERE user_id = %s", (unique_id,))
        count = cur.fetchone()
    return {"followers_count": count[0]}

@app.get("/following_count/{unique_id}")
def get_following_count(unique_id: str, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM followers WHERE follower_id = %s", (unique_id,))
        count = cur.fetchone()
    return {"following_count": count[0]}



@app.get("/followers/{user_id}")
def get_followers(user_id: str, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("""
            SELECT register_details.name, register_details.email 
            FROM followers 
            JOIN register_details ON followers.follower_id = register_details.unique_id 
            WHERE followers.user_id = %s
        """, (user_id,))
        followers = cur.fetchall()
        result= [ {"name":row[0], "email": row[1]} for row in followers]
    return {"followers": result}

@app.get("/following/{follower_id}")
def get_following(follower_id: str, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("""
            SELECT register_details.name, register_details.email 
            FROM followers 
            JOIN register_details ON followers.user_id = register_details.unique_id 
            WHERE followers.follower_id = %s
        """, (follower_id,))
        following = cur.fetchall()
        result= [ {"name":row[0], "email": row[1]} for row in following]
    return {"following": result}



@app.get("/get_unique_id/{name}", response_model=dict)
def get_unique_id(name: str, db=Depends(get_db)):
    with db.cursor() as cur:
        name=unquote(name)
        print(name,'srr')
        cur.execute("SELECT * FROM register_details WHERE name = %s", (name,))
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Student not found")
        return {"unique_id": result[0],"Name":result[1],"Email":result[2]}
    

@app.get("/check_follow/{user_unique_id}/{target_unique_id}", response_model=dict)
def check_follow(user_unique_id: str, target_unique_id: str, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM followers WHERE user_id = %s AND follower_id = %s",
            (target_unique_id,user_unique_id,)
        )
        count = cur.fetchone()
        return {"isFollowing": bool(count[0])}
    


@app.get("/videos/following/{user_unique_id}")
def get_following_videos(user_unique_id: str, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("""
            SELECT v.video_path,f.user_id,v.likes,v.id,v.name  FROM videos v
            JOIN followers f ON f.user_id = v.unique_id
            WHERE f.follower_id = %s
        """, (user_unique_id,))
        video_data = cur.fetchall()
        result = [{"video_path": row[0], "likes": row[2], "user_id": row[1],"id":row[3],'name':row[4]} for row in video_data]
        return {"result": result}
        



@app.get("/images/following/{user_unique_id}")
def get_following_videos(user_unique_id: str, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("""
            SELECT v.image_path,f.user_id,v.likes,v.id,v.name  FROM images v
            JOIN followers f ON f.user_id = v.unique_id
            WHERE f.follower_id = %s
        """, (user_unique_id,))
        video_data = cur.fetchall()
        result = [{"image_path": row[0], "likes": row[2], "user_id": row[1],"id":row[3],'name':row[4]} for row in video_data]
        return {"result": result}
    

@app.get("/images/check_likes1/{unique_id}")
def get_image_likes(unique_id:str,db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(""" 
               select * from imageslike """)
        image_data=cur.fetchall()
        result = [{"image_path": row[1], "liked": row[2], "unique_id": row[3],"user_id": row[4],"id":row[0]} for row in image_data]
        return {"result": result}
    

@app.get("/videos/check_likes1/{unique_id}")
def get_image_likes2(db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(""" 
               select * from videoslike """)
        image_data=cur.fetchall()
        result = [{"video_path": row[1], "liked": row[2], "unique_id": row[3],"user_id": row[4],"id":row[0]} for row in image_data]
        return {"result": result}
    

@app.get("/youtube_videos/check_likes1/{unique_id}")
def get_image_likes2(db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(""" 
               select * from youtube_videoslike """)
        image_data=cur.fetchall()
        result = [{"youtube_path": row[1], "liked": row[2], "unique_id": row[3],"user_id": row[4],"id":row[0]} for row in image_data]
        return {"result": result}
    


          
@app.get("/get_id/{unique_id}", response_model=dict)
def get_unique_id(unique_id: str, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM register_details WHERE unique_id = %s", (unique_id,))
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Student not found")
        return {"unique_id": result[0],"Name":result[1],"Email":result[2]}
    

@app.get("/get_is_membership_form_filled/{unique_id}", response_model=dict)
def get_is_membership_form_filled(unique_id: str, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM register_details WHERE unique_id = %s", (unique_id,))
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Student not found")
        return {"unique_id": result[0],"is_membership_form_filled":result[13]}
    

@app.get("/get_user_email/{unique_id}", response_model=dict)
def get_user_email(unique_id: str, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM register_details WHERE unique_id = %s", (unique_id,))
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Student not found")
        return {"unique_id": result[0],"email":result[2]}



@app.get("/general/get_images/{unique_id}", response_model=dict)
def general_images(unique_id: str, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM images WHERE unique_id != %s", (unique_id,))
        results = cur.fetchall()
        if not results:
            raise HTTPException(status_code=404, detail="Student not found")
        result1=[{"unique_id": result[1],"id":result[0],"image_path":result[2],"likes":result[3],'name':result[5]} for result in results]
        return {"result":result1}
    

@app.get("/general/get_videos/{unique_id}", response_model=dict)
def general_images(unique_id: str, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM videos WHERE unique_id != %s", (unique_id,))
        results = cur.fetchall()
        if not results:
            raise HTTPException(status_code=404, detail="Student not found")
        result1=[{"unique_id": result[1],"id":result[0],"video_path":result[2],"likes":result[3],'name':result[5]} for result in results]
        return {"result":result1}
    


@app.get("/general/get_youtube_videos/{unique_id}", response_model=dict)
def general_images(unique_id: str, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM youtube_videos WHERE unique_id != %s", (unique_id,))
        results = cur.fetchall()
        if not results:
            raise HTTPException(status_code=404, detail="Student not found")
        result1=[{"unique_id": result[1],"id":result[0],"youtube_path":result[2],"likes":result[3],'name':result[4]} for result in results]
        return {"result":result1}
    

@app.get("/top_five_results/",response_model=dict)
def top_five_results(db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM votingvedios ORDER BY likes DESC LIMIT 5", ())
        results = cur.fetchall()
        result1=[{"name": result[1],"id":result[0],"youtube_path":result[3],"likes":result[4],'clg':result[5],'descrpt':result[6]} for result in results]
        return {"result":result1}
    
@app.get("/top_five_results_dance/",response_model=dict)
def top_five_results(db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM dancevotingvideos ORDER BY likes DESC LIMIT 5", ())
        results = cur.fetchall()
        result1=[{"name": result[1],"id":result[0],"youtube_path":result[3],"likes":result[4],'clg':result[5],'descrpt':result[6]} for result in results]
        return {"result":result1}
    
@app.get("/top_five_results_photo/",response_model=dict)
def top_five_results(db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM photovotingvideos ORDER BY likes DESC LIMIT 5", ())
        results = cur.fetchall()
        result1=[{"name": result[1],"id":result[0],"youtube_path":result[3],"likes":result[4],'clg':result[5],'descrpt':result[6]} for result in results]
        return {"result":result1}
    
@app.get("/top_five_results_fashion/",response_model=dict)
def top_five_results(db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM fashionvotingvideos ORDER BY likes DESC LIMIT 5", ())
        results = cur.fetchall()
        result1=[{"name": result[1],"id":result[0],"youtube_path":result[3],"likes":result[4],'clg':result[5],'descrpt':result[6]} for result in results]
        return {"result":result1}

@app.get("/top_five_results_standup/",response_model=dict)
def top_five_results(db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM standupvotingvideos ORDER BY likes DESC LIMIT 5", ())
        results = cur.fetchall()
        result1=[{"name": result[1],"id":result[0],"youtube_path":result[3],"likes":result[4],'clg':result[5],'descrpt':result[6]} for result in results]
        return {"result":result1}

@app.get("/top_five_results_singing/",response_model=dict)
def top_five_results(db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM singingvotingvideos ORDER BY likes DESC LIMIT 5", ())
        results = cur.fetchall()
        result1=[{"name": result[1],"id":result[0],"youtube_path":result[3],"likes":result[4],'clg':result[5],'descrpt':result[6]} for result in results]
        return {"result":result1}

@app.get("/top_five_results_acting/",response_model=dict)
def top_five_results(db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM actingvotingvideos ORDER BY likes DESC LIMIT 5", ())
        results = cur.fetchall()
        result1=[{"name": result[1],"id":result[0],"youtube_path":result[3],"likes":result[4],'clg':result[5],'descrpt':result[6]} for result in results]
        return {"result":result1}
    


@app.get("/get_user_details/{unique_id}",response_model=dict)
def get_user_details(unique_id:str, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM details where unique_id=%s", (unique_id,))
        results = cur.fetchall()
        result1=[{"role": result[6],"id":result[0],"profile_image":result[1],"cover_image":result[2],'about_you': result[3],'clg':result[4],'acheivements':result[5]} for result in results]
        return {"result":result1}
    

@app.get("/get_user_profile_details",response_model=dict)
def get_user_profile_details( db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM details ")
        results = cur.fetchall()
        result1=[{"profile_image":result[1],"user_id":result[7]} for result in results]
        return {"result":result1}
    

    




    


    
    




    

     




    



    



    





    









# -------------------------------------------------------------------PUT METHOD ---------------------------------------------------------------------

@app.put("/images/likes/")
def increase_like_count(like_data: LikeUpdate,  db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("START TRANSACTION")
        # Update the like count for the specified image
        cur.execute(
            """ UPDATE images SET likes = likes + 1 WHERE unique_id=%s and id=%s """,
            (like_data.user_id,like_data.id ,) 
        )
        if cur.rowcount == 0:
            cur.execute("ROLLBACK")
            raise HTTPException(status_code=404, detail="Image not found")

        
        cur.execute(
            """INSERT INTO imageslike (image_path, Liked,unique_id,user_id) VALUES (%s, True ,%s,%s)""",
            ( like_data.image_path,like_data.unique_id,like_data.user_id,)
        )

        cur.execute("COMMIT")
       
        return {"message": "Like count increased successfully"}
    


    
@app.put("/add_membership_details/{unique_id}", response_model=dict)
def add_membership_data(unique_id: str, membership_data: MembershipData, db=Depends(get_db)):
    with db.cursor() as cur:
        # SQL query to update all fields for a student with the given unique_id
        sql_query = """
            UPDATE register_details
            SET 
                ismembershipformfilled = %s,
                address = %s,
                gender = %s,
                college = %s,
                referralsource = %s,
                reasontojoin = %s,
                interests = %s
            WHERE unique_id = %s
        """
        
        # Execute the query with all values provided
        cur.execute(sql_query, 
            (True, 
            membership_data.address,
            membership_data.gender,
            membership_data.college,
            membership_data.referralsource,
            membership_data.reasontojoin,
            membership_data.interests,
            unique_id))
        cur.execute("COMMIT")

        return {"message": "Student membership details added successfully"}






@app.put("/update_user_details/{user_id}")
def submit_form_data(
    user_id:str,
    role: str = Form(...),
    about_you: str = Form(...),
    clg: str = Form(...),
    achievements: str = Form(...),
    profile_image: UploadFile = File(...),
    cover_image: UploadFile = File(...),
    db=Depends(get_db)
):
        with db.cursor() as cur:
            
            file_content = read_file_content(profile_image)
            resp = vercel_blob.put(profile_image.filename, file_content)
            file_url_image = resp.get("url")

            file_content2 = read_file_content(cover_image)
            resp1 = vercel_blob.put(cover_image.filename, file_content2)
            file_url_video = resp1.get("url")


            cur.execute(
                "UPDATE details SET name=%s, profile_image=%s, cover_image=%s, about_you=%s, studies=%s, achievements=%s WHERE unique_id=%s",
                (role, file_url_image, file_url_video,
                 about_you, clg, achievements, user_id ,))
            cur.execute("COMMIT")
            return {"message": "User details updated successfully"}
        


   
    
@app.put("/videos/likes/")
def increase_like_count(like_data: LikeUpdate2,  db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("START TRANSACTION")
        # Update the like count for the specified image
        cur.execute(
            """ UPDATE videos SET likes = likes + 1 WHERE unique_id=%s and id=%s """,
            (like_data.user_id,like_data.id,) 
        )
        if cur.rowcount == 0:
            cur.execute("ROLLBACK")
            raise HTTPException(status_code=404, detail="Image not found")

        
        cur.execute(
            """INSERT INTO videoslike (video_path, Liked,unique_id,user_id) VALUES (%s, True ,%s,%s)""",
            ( like_data.video_path,like_data.unique_id,like_data.user_id,)
        )

        cur.execute("COMMIT")
       
        return {"message": "Like count increased successfully"}
    


@app.put("/youtube_videos/likes/")
def increase_like_count(like_data: LikeUpdate3,  db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("START TRANSACTION")
        # Update the like count for the specified image
        cur.execute(
            """ UPDATE youtube_videos SET likes = likes + 1 WHERE unique_id=%s and id=%s """,
            (like_data.user_id,like_data.id) 
        )
        if cur.rowcount == 0:
            cur.execute("ROLLBACK")
            raise HTTPException(status_code=404, detail="Image not found")

        
        cur.execute(
            """INSERT INTO youtube_videoslike (youtube_path, Liked,unique_id,user_id) VALUES (%s, True ,%s,%s)""",
            ( like_data.youtube_path,like_data.unique_id,like_data.user_id,)
        )

        cur.execute("COMMIT")
       
        return {"message": "Like count increased successfully"}


    
@app.put("/voting_videos/likes/{id}")
def increase_like_count(id: int,  db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("START TRANSACTION")
        # Update the like count for the specified image
        cur.execute(
            """ UPDATE votingvedios SET likes = likes + 1 WHERE  id=%s """,
            (id,) 
        )
        if cur.rowcount == 0:
            cur.execute("ROLLBACK")
            raise HTTPException(status_code=404, detail="Image not found")

        
       
        cur.execute("COMMIT")
        return {"message": "Like count increased successfully"}

@app.put("/dancevoting_videos/likes/{id}")
def increase_like_count(id: int,  db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("START TRANSACTION")
        # Update the like count for the specified image
        cur.execute(
            """ UPDATE dancevotingvideos SET likes = likes + 1 WHERE  id=%s """,
            (id,) 
        )
        if cur.rowcount == 0:
            cur.execute("ROLLBACK")
            raise HTTPException(status_code=404, detail="Image not found")

        
       
        cur.execute("COMMIT")
        return {"message": "Like count increased successfully"}
    
@app.put("/photovoting_videos/likes/{id}")
def increase_like_count(id: int,  db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("START TRANSACTION")
        # Update the like count for the specified image
        cur.execute(
            """ UPDATE photovotingvideos SET likes = likes + 1 WHERE  id=%s """,
            (id,) 
        )
        if cur.rowcount == 0:
            cur.execute("ROLLBACK")
            raise HTTPException(status_code=404, detail="Image not found")

        
       
        cur.execute("COMMIT")
        return {"message": "Like count increased successfully"}
    
@app.put("/fashionvoting_videos/likes/{id}")
def increase_like_count(id: int,  db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("START TRANSACTION")
        # Update the like count for the specified image
        cur.execute(
            """ UPDATE fashionvotingvideos SET likes = likes + 1 WHERE  id=%s """,
            (id,) 
        )
        if cur.rowcount == 0:
            cur.execute("ROLLBACK")
            raise HTTPException(status_code=404, detail="Image not found")

        
       
        cur.execute("COMMIT")
        return {"message": "Like count increased successfully"}
    
@app.put("/standupvoting_videos/likes/{id}")
def increase_like_count(id: int,  db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("START TRANSACTION")
        # Update the like count for the specified image
        cur.execute(
            """ UPDATE standupvotingvideos SET likes = likes + 1 WHERE  id=%s """,
            (id,) 
        )
        if cur.rowcount == 0:
            cur.execute("ROLLBACK")
            raise HTTPException(status_code=404, detail="Image not found")

        
       
        cur.execute("COMMIT")
        return {"message": "Like count increased successfully"}
    
@app.put("/singingvoting_videos/likes/{id}")
def increase_like_count(id: int,  db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("START TRANSACTION")
        # Update the like count for the specified image
        cur.execute(
            """ UPDATE singingvotingvideos SET likes = likes + 1 WHERE  id=%s """,
            (id,) 
        )
        if cur.rowcount == 0:
            cur.execute("ROLLBACK")
            raise HTTPException(status_code=404, detail="Image not found")

        
       
        cur.execute("COMMIT")
        return {"message": "Like count increased successfully"}
    
@app.put("/actingvoting_videos/likes/{id}")
def increase_like_count(id: int,  db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("START TRANSACTION")
        # Update the like count for the specified image
        cur.execute(
            """ UPDATE actingvotingvideos SET likes = likes + 1 WHERE  id=%s """,
            (id,) 
        )
        if cur.rowcount == 0:
            cur.execute("ROLLBACK")
            raise HTTPException(status_code=404, detail="Image not found")

        
       
        cur.execute("COMMIT")
        return {"message": "Like count increased successfully"}
    

@app.put('/password_change')
def password_change(items:PasswordChange,db=Depends(get_db)):
     with db.cursor() as cur:
        cur.execute(
            """ select * from register_details where email=%s """,
            (items.email,) 
        )
        if cur.rowcount == 0:
            cur.execute("ROLLBACK")
            raise HTTPException(status_code=404, detail="student details not found , pls register if you don't have account")
        
        cur.execute(
            """ update register_details set password=%s where email=%s """,
            (items.password,items.email,) 
        )
        cur.execute("COMMIT")
        return {"message": "Password updated sucessfully, pls login"}









# ---------------------------------------------------------------------DELETE METHOD--------------------------------------------------------------------

@app.delete("/images/unlikes/")
def decrease_like_count(dislike:LikeUpdate, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("START TRANSACTION")
        # Decrease the like count for the specified image
        cur.execute(
            """UPDATE images SET likes = likes - 1 WHERE unique_id = %s AND id = %s""",
            (dislike.user_id, dislike.id)
        )
        if cur.rowcount == 0:
            cur.execute("ROLLBACK")
            raise HTTPException(status_code=404, detail="Image not found")
        

        cur.execute(
            """DELETE from imageslike where image_path=%s and user_id=%s and unique_id=%s""",
            (dislike.image_path, dislike.user_id, dislike.unique_id,)
        )
        db.commit()
        return {"message": "Like count decreased successfully"}
    


@app.delete("/videos/unlikes/")
def decrease_like_count(dislike:LikeUpdate2, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("START TRANSACTION")
        # Decrease the like count for the specified image
        cur.execute(
            """UPDATE videos SET likes = likes - 1 WHERE unique_id = %s AND id = %s""",
            (dislike.user_id, dislike.id)
        )
        if cur.rowcount == 0:
            cur.execute("ROLLBACK")
            raise HTTPException(status_code=404, detail="Image not found")
        

        cur.execute(
            """DELETE from videoslike where video_path=%s and user_id=%s and unique_id=%s""",
            (dislike.video_path, dislike.user_id, dislike.unique_id,)
        )
        db.commit()
        return {"message": "Like count decreased successfully"}
    


@app.delete("/youtube_videos/unlikes/")
def decrease_count(dislike: LikeUpdate3,  db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("START TRANSACTION")
        # Update the like count for the specified image
        cur.execute(
            """ UPDATE youtube_videos SET likes = likes - 1 WHERE unique_id=%s and id=%s """,
            (dislike.user_id,dislike.id) 
        )
        if cur.rowcount == 0:
            cur.execute("ROLLBACK")
            raise HTTPException(status_code=404, detail="Image not found")

        
        cur.execute(
            """DELETE from youtube_videoslike where youtube_path=%s and user_id=%s and unique_id=%s""",
            (dislike.youtube_path, dislike.user_id, dislike.unique_id,)
        )

        cur.execute("COMMIT")
       
        return {"message": "Like count increased successfully"}

    






@app.delete("/delete_image/{unique_id}/{id}")
def delete_image(unique_id: str, id: int, db=Depends(get_db)):
    with db.cursor() as cur:

        cur.execute("DELETE FROM images WHERE unique_id = %s AND id = %s", (unique_id, id))
        db.commit()

    return JSONResponse(status_code=200, content={"message": "Image deleted successfully"})

# Endpoint to delete a video
@app.delete("/delete_video/{unique_id}/{id}")
def delete_video(unique_id: str, id: int, db=Depends(get_db)):
    with db.cursor() as cur:
       
        cur.execute("DELETE FROM videos WHERE unique_id = %s AND id = %s", (unique_id, id,))
        db.commit()

    return JSONResponse(status_code=200, content={"message": "Video deleted successfully"})


@app.delete("/delete_youtube/{unique_id}/{id}")
def delete_image(unique_id: str, id: int, db=Depends(get_db)):
    with db.cursor() as cur:

        cur.execute("DELETE FROM youtube_videos WHERE unique_id = %s AND id = %s", (unique_id, id,))
        db.commit()

    return JSONResponse(status_code=200, content={"message": "Image deleted successfully"})


@app.delete("/follow", response_model=dict)
def unfollow(follow_request: FollowRequest, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM followers WHERE user_id = %s AND follower_id = %s",
            (follow_request.user_id, follow_request.follower_id,)
        )
        db.commit()
    return {"message": "Unfollowed successfully"}



@app.delete("/delete_voting_video/{id}", response_model=dict)
def delete_voting_video(id: int, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM votingvedios WHERE id = %s ",
            (id,)
        )
        db.commit()
    return {"message": "deleted successfully"}

@app.delete("/delete_dance_voting_video/{id}", response_model=dict)
def delete_voting_video(id: int, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM dancevotingvideos WHERE id = %s ",
            (id,)
        )
        db.commit()
    return {"message": "deleted successfully"}

@app.delete("/delete_photo_voting_video/{id}", response_model=dict)
def delete_voting_video(id: int, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM photovotingvideos WHERE id = %s ",
            (id,)
        )
        db.commit()
    return {"message": "deleted successfully"}

@app.delete("/delete_fashion_voting_video/{id}", response_model=dict)
def delete_voting_video(id: int, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM fashionvotingvideos WHERE id = %s ",
            (id,)
        )
        db.commit()
    return {"message": "deleted successfully"}

@app.delete("/delete_standup_voting_video/{id}", response_model=dict)
def delete_voting_video(id: int, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM standupvotingvideos WHERE id = %s ",
            (id,)
        )
        db.commit()
    return {"message": "deleted successfully"}

@app.delete("/delete_singing_voting_video/{id}", response_model=dict)
def delete_voting_video(id: int, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM singingvotingvideos WHERE id = %s ",
            (id,)
        )
        db.commit()
    return {"message": "deleted successfully"}

@app.delete("/delete_acting_voting_video/{id}", response_model=dict)
def delete_voting_video(id: int, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM actingvotingvideos WHERE id = %s ",
            (id,)
        )
        db.commit()
    return {"message": "deleted successfully"}











