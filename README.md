# FindIt

FindIt is a Django lost-and-found web app for posting lost items, sharing found items, chatting with other users, and verifying claims before an item is returned.

## What It Does

- User registration, login, and logout
- Lost and found item listings
- Item detail pages with edit and delete actions
- Posting new items
- Claim workflow with verification photos and status tracking
- Chat between users about items and claims
- Profile and dashboard pages
- Admin area for managing data

## Main App Routes

The project root routes to the `items` app.

- `/` - home page
- `/welcome/` - welcome page
- `/login/` - user login
- `/register/` - user registration
- `/logout/` - log out
- `/dashboard/` - user dashboard
- `/profile/` - profile page
- `/lost-items/` - lost items list
- `/found-items/` - found items list
- `/post/` - create a new item
- `/item/<id>/` - item details
- `/item/<id>/edit/` - edit item
- `/item/<id>/delete/` - delete item
- `/item/<id>/claim/` - claim an item
- `/claim/<id>/verify/` - verify a claim
- `/chats/` - chat list
- `/item/<id>/chat/` - start a chat for an item
- `/chat/<id>/` - chat detail
- `/chat/<id>/end/` - end a chat

## Setup And Run

From the folder that contains `manage.py`:

```powershell
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

If `python` is not recognized on your machine, use the full path to the Python executable:

```powershell
C:/Users/manem/AppData/Local/Programs/Python/Python313/python.exe manage.py migrate
C:/Users/manem/AppData/Local/Programs/Python/Python313/python.exe manage.py runserver 127.0.0.1:8000
```

Then open:

```text
http://127.0.0.1:8000/
```

## Useful Checks

```powershell
python manage.py check
```

## Sample Data And Admin

This project includes helper management commands:

- `python manage.py create_admin` - creates an admin account with sample credentials
- `python manage.py add_sample_data` - adds sample lost and found items

Default admin credentials from the helper command:

- Username: `admin`
- Password: `admin123`
- Admin URL: `/admin/`

## Database And Media

- Uses SQLite database: `db.sqlite3`
- User uploads are stored in `media/`
- Media files are served during development only

## Project Structure

- `findit/` - Django project settings and URL configuration
- `items/` - main application code, models, views, templates, and management commands
- `items/templates/items/` - HTML templates
- `items/static/items/` - app CSS and static assets

## Notes

- The project uses a custom user model: `items.CustomUser`
- The app is configured for local development with `DEBUG = True`
- Before pushing to GitHub, make sure the app runs cleanly with `python manage.py check` and `python manage.py runserver`