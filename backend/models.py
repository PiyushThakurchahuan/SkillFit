from pydantic import BaseModel, Field
class Profile(BaseModel):
    name:str; email:str=''; education:str=''; experience:float=Field(0,ge=0); career_break:float=Field(0,ge=0); location:str=''; work_mode:str='Any'; target_role:str=''; skills:list[str]=[]
class Assessment(BaseModel):
    profile_id:int; role:str; score:float=Field(ge=0,le=100)
