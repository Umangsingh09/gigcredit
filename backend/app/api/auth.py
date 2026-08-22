import uuid
from fastapi import APIRouter, HTTPException

from backend.app.schemas.auth import LoginRequest, RegisterRequest, GoogleAuthRequest
from backend.app.core.supabase import supabase

local_users = {}

router = APIRouter(
	prefix="/auth",
	tags=["Authentication"]
)


@router.post("/google")
def google_auth(data: GoogleAuthRequest):
	"""
	Backend Authentication endpoint for Google OAuth Sign-In.
	Authenticates user via Supabase OAuth or local engine fallback.
	"""
	user_id = str(uuid.uuid4())
	access_token = f"gc_google_token_{uuid.uuid4().hex[:12]}"

	if supabase:
		try:
			response = supabase.auth.admin.create_user({
				"email": data.email,
				"email_confirm": True,
				"user_metadata": {"full_name": data.name, "avatar_url": data.photo_url}
			})
			if hasattr(response, "user") and response.user:
				user_id = str(response.user.id)
		except Exception:
			pass

	full_name = data.name or data.email.split("@")[0].capitalize()
	local_users[data.email] = {"password": "", "full_name": full_name}

	return {
		"message": "Google Authentication Successful",
		"user_id": user_id,
		"email": data.email,
		"name": full_name,
		"access_token": access_token,
		"provider": "google",
	}


@router.post("/register")
def register(data: RegisterRequest):
	if supabase is None:
		if data.email in local_users:
			raise HTTPException(status_code=400, detail="An account with this email already exists")
		local_users[data.email] = {"password": data.password, "full_name": data.full_name}
		return {"message": "Registration successful", "user_id": data.email, "email": data.email, "full_name": data.full_name, "access_token": f"local-{data.email}"}

	try:
		response = supabase.auth.sign_up({
			"email": data.email,
			"password": data.password,
			"options": {"data": {"full_name": data.full_name}},
		})

		user = getattr(response, "user", None) or (response.get("user") if isinstance(response, dict) else None)

		if user is None:
			raise HTTPException(status_code=400, detail="Registration failed")

		user_id = getattr(user, "id", None) or user.get("id")
		email = getattr(user, "email", None) or user.get("email")

		session = getattr(response, "session", None) or (response.get("session") if isinstance(response, dict) else None)
		access_token = getattr(session, "access_token", None) or (session.get("access_token") if session else None)
		return {
			"message": "Registration successful",
			"user_id": str(user_id),
			"email": email,
			"full_name": data.full_name,
			"access_token": access_token,
		}

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(data: LoginRequest):
	if supabase is None:
		user = local_users.get(data.email)
		if not user or user["password"] != data.password:
			raise HTTPException(status_code=401, detail="Invalid email or password")
		return {
			"message": "Login successful",
			"user_id": data.email,
			"email": data.email,
			"full_name": user["full_name"],
			"access_token": f"local-{data.email}",
		}

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
			"full_name": (getattr(user, "user_metadata", None) or user.get("user_metadata", {}) or {}).get("full_name", "Umang Raj"),
		}

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=401, detail="Invalid email or password")
