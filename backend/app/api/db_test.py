# from fastapi import APIRouter, Depends
# from sqlalchemy import text
# from sqlalchemy.orm import Session
# from backend.app.core.database import get_db

# router=APIRouter()

# @router.get("/db-test")
# def db_test(db: Session = Depends(get_db)):
#     result = db.execute(text("SELECT 1")).scalar()
#     return {"db_response":result}

# """
# 🧠 What this code does (VERY IMPORTANT)
# Line	                     Purpose
# Depends(get_db)	            Opens DB session
# text("SELECT 1")	        Raw SQL test
# execute()	                Runs SQL via psycopg
# scalar()	                Gets value 1
# finally db.close()	        Happens automatically

# If this works → DB layer is correct.
# """