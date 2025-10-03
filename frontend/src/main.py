import flet as ft
from api_client import ResumeAPI
import os

class ResumeApp:
    def __init__(self):
        self.api = ResumeAPI()
        self.current_user = None
        
    def main(self, page: ft.Page):
        page.title = "Resume Review App"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.favicon = "icons/favicon.png"
        page.padding = 20
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        # UI Components
        self.login_username = ft.TextField(label="Username", width=300)
        self.login_password = ft.TextField(label="Password", password=True, width=300)
        self.login_btn = ft.ElevatedButton("Login", on_click=self.login_clicked)
        self.login_status = ft.Text()
        
        self.register_username = ft.TextField(label="Username", width=300)
        self.register_password = ft.TextField(label="Password", password=True, width=300)
        self.register_email = ft.TextField(label="Email", width=300)
        self.register_github = ft.TextField(label="GitHub URL", width=300)
        self.register_btn = ft.ElevatedButton("Register", on_click=self.register_clicked)
        self.register_status = ft.Text()
        
        self.file_picker = ft.FilePicker(on_result=self.file_picker_result)
        self.upload_btn = ft.ElevatedButton("Upload Resume", on_click=self.upload_clicked)
        self.upload_status = ft.Text()
        self.selected_file = ft.Text("No file selected")
        
        self.resumes_list = ft.ListView(expand=1, spacing=10, padding=20)
        self.refresh_btn = ft.ElevatedButton("Refresh Resumes", on_click=self.refresh_resumes)
        
        self.logout_btn = ft.ElevatedButton("Logout", on_click=self.logout_clicked)
        
        # Tabs for different sections
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Login",
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Login to your account", size=20, weight=ft.FontWeight.BOLD),
                            self.login_username,
                            self.login_password,
                            self.login_btn,
                            self.login_status
                        ])
                    )
                ),
                ft.Tab(
                    text="Register",
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Create new account", size=20, weight=ft.FontWeight.BOLD),
                            self.register_username,
                            self.register_password,
                            self.register_email,
                            self.register_github,
                            self.register_btn,
                            self.register_status
                        ])
                    )
                ),
                ft.Tab(
                    text="Resumes",
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Manage your resumes", size=20, weight=ft.FontWeight.BOLD),
                            self.selected_file,
                            ft.Row([self.upload_btn, self.refresh_btn]),
                            self.upload_status,
                            self.resumes_list
                        ])
                    )
                )
            ]
        )
        
        # Add file picker to page (hidden)
        page.overlay.append(self.file_picker)
        
        # Main layout
        page.add(
            ft.Column([
                ft.Row([
                    ft.Text("Resume Review App", size=24, weight=ft.FontWeight.BOLD),
                    self.logout_btn
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.tabs
            ])
        )
        
        # Check if user is already logged in
        self.check_auth_status()
    
    def check_auth_status(self):
        """Check if user has valid token"""
        if self.api.access_token:
            self.show_snackbar("Already logged in")
            self.refresh_resumes(None)
    
    def login_clicked(self, e):
        """Handle login button click"""
        username = self.login_username.value
        password = self.login_password.value
        
        if not username or not password:
            self.login_status.value = "Please fill all fields"
            self.login_status.update()
            return
        
        self.login_btn.disabled = True
        self.login_btn.text = "Logging in..."
        self.login_btn.update()
        
        # Call API
        result = self.api.login(username, password)
        
        if result["success"]:
            self.login_status.value = "Login successful!"
            self.login_status.color = ft.Colors.GREEN
            self.current_user = username
            self.show_snackbar(f"Welcome {username}!")
            self.refresh_resumes(None)
        else:
            self.login_status.value = f"Error: {result['error']}"
            self.login_status.color = ft.Colors.RED
        
        self.login_btn.disabled = False
        self.login_btn.text = "Login"
        self.login_btn.update()
        self.login_status.update()
    
    def register_clicked(self, e):
        """Handle register button click"""
        username = self.register_username.value
        password = self.register_password.value
        email = self.register_email.value
        github = self.register_github.value
        
        if not username or not password or not email:
            self.register_status.value = "Please fill required fields"
            self.register_status.update()
            return
        
        self.register_btn.disabled = True
        self.register_btn.text = "Registering..."
        self.register_btn.update()
        
        # Call API
        result = self.api.register(username, password, email, github)
        
        if result["success"]:
            self.register_status.value = "Registration successful!"
            self.register_status.color = ft.Colors.GREEN
            self.show_snackbar("Account created successfully!")
            # Switch to login tab
            self.tabs.selected_index = 0
            self.tabs.update()
        else:
            self.register_status.value = f"Error: {result['error']}"
            self.register_status.color = ft.Colors.RED
        
        self.register_btn.disabled = False
        self.register_btn.text = "Register"
        self.register_btn.update()
        self.register_status.update()
    
    def upload_clicked(self, e):
        """Handle upload button click"""
        if not self.api.access_token:
            self.show_snackbar("Please login first")
            return
        
        self.file_picker.pick_files(
            allowed_extensions=["pdf"],
            type=ft.FilePickerFileType.CUSTOM
        )
    
    def file_picker_result(self, e: ft.FilePickerResultEvent):
        """Handle file selection result"""
        if e.files:
            file_path = e.files[0].path
            self.selected_file.value = f"Selected: {e.files[0].name}"
            self.selected_file.update()
            
            # Upload the file
            self.upload_btn.disabled = True
            self.upload_btn.text = "Uploading..."
            self.upload_btn.update()
            
            result = self.api.upload_resume(file_path)
            
            if result["success"]:
                self.upload_status.value = "Upload successful!"
                self.upload_status.color = ft.Colors.GREEN
                self.show_snackbar("Resume uploaded successfully!")
                self.refresh_resumes(None)
            else:
                self.upload_status.value = f"Error: {result['error']}"
                self.upload_status.color = ft.Colors.RED
            
            self.upload_btn.disabled = False
            self.upload_btn.text = "Upload Resume"
            self.upload_btn.update()
            self.upload_status.update()
    
    def refresh_resumes(self, e):
        """Refresh resumes list"""
        if not self.api.access_token:
            self.resumes_list.controls.clear()
            self.resumes_list.controls.append(ft.Text("Please login to view resumes"))
            self.resumes_list.update()
            return
        
        result = self.api.get_my_resumes()
        
        self.resumes_list.controls.clear()
        
        if result["success"]:
            resumes = result["data"]
            if resumes:
                for resume in resumes:
                    self.resumes_list.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Text(f"File: {resume.get('file_name', 'N/A')}", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"Size: {resume.get('file_size', 0)} bytes"),
                                    ft.Text(f"Uploaded: {resume.get('upload_date', 'N/A')}"),
                                ]),
                                padding=10
                            )
                        )
                    )
            else:
                self.resumes_list.controls.append(ft.Text("No resumes found"))
        else:
            self.resumes_list.controls.append(ft.Text(f"Error: {result['error']}"))
        
        self.resumes_list.update()
    
    def logout_clicked(self, e):
        """Handle logout button click"""
        if self.api.access_token:
            result = self.api.logout()
            if result["success"]:
                self.show_snackbar("Logged out successfully")
            else:
                self.show_snackbar(f"Logout error: {result['error']}")
        
        self.current_user = None
        self.login_status.value = ""
        self.register_status.value = ""
        self.upload_status.value = ""
        self.selected_file.value = "No file selected"
        self.resumes_list.controls.clear()
        self.resumes_list.controls.append(ft.Text("Please login to view resumes"))
        
        self.login_status.update()
        self.register_status.update()
        self.upload_status.update()
        self.selected_file.update()
        self.resumes_list.update()
    
    def show_snackbar(self, message: str):
        """Show snackbar message"""
        # You can implement snackbar functionality here
        print(f"Snackbar: {message}")

# Run the app
if __name__ == "__main__":
    app = ResumeApp()
    BASE_DIR = os.path.dirname(__file__)
    ft.app(
        target=app.main,
        assets_dir=os.path.join(BASE_DIR, "assets"),
        view=ft.WEB_BROWSER,
        host="0.0.0.0",
        port=8080
        )
