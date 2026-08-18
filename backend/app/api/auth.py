from fastapi import APIRouter, HTTPException

from backend.app.schemas.auth import RegisterRequest, LoginRequest
from backend.app.core.supabase import supabase

router = APIRouter(
	prefix="/auth",
	tags=["Authentication"]
)

@router.post("/register")
def register(data: RegisterRequest):
	try:
		response = supabase.auth.sign_up({
			"email": data.email,
			"password": data.password
		})

		user = getattr(response, "user", None) or (response.get("user") if isinstance(response, dict) else None)

		if user is None:
			raise HTTPException(status_code=400, detail="Registration failed")

		user_id = getattr(user, "id", None) or user.get("id")
		email = getattr(user, "email", None) or user.get("email")

		return {
			"message": "Registration successful",
			"user_id": str(user_id),
			"email": email,
		}

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(data: LoginRequest):
	try:
		response = supabase.auth.sign_in_with_password({
			"email": data.email,
			"password": data.password
		})

		user = getattr(response, "user", None) or (response.get("user") if isinstance(response, dict) else None)
		session = getattr(response, "session", None) or (response.get("session") if isinstance(response, dict) else None)

		if user is None or session is None:
			raise HTTPException(status_code=401, detail="Invalid email or password")

		user_id = getattr(user, "id", None) or user.get("id")
		email = getattr(user, "email", None) or user.get("email")
		access_token = getattr(session, "access_token", None) or session.get("access_token")

		return {
			"message": "Login successful",
			"user_id": str(user_id),
			"email": email,
			"access_token": access_token,
		}

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=401, detail="Invalid email or password")
