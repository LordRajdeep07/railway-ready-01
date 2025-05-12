@server.route("/auth/google/callback")
def google_callback():
    """Handle Google OAuth callback."""
    try:
        # Get the auth code from the request
        auth_code = request.args.get('code')
        if not auth_code:
            flash("Authentication failed: No authorization code received", "error")
            return redirect("/login")
            
        # Exchange the auth code for credentials
        # Create a user with the information from Google
        email = request.args.get('email')
        name = request.args.get('name')
        
        if not email:
            flash("Authentication failed: No email received", "error")
            return redirect("/login")
        
        # Check if user exists
        try:
            user = auth.get_user_by_email(email)
        except auth.UserNotFoundError:
            # Create the user if they don't exist
            user = auth.create_user(
                email=email,
                display_name=name,
                email_verified=True
            )
        
        # Create User object
        user_obj = User(
            uid=user.uid,
            username=user.display_name or email.split('@')[0],
            email=user.email,
            is_verified=True
        )
        
        # Login user
        login_user(user_obj)
        return redirect("/dashboard")
        
    except Exception as e:
        flash(f"Google authentication failed: {str(e)}", "error")
        return redirect("/login") 