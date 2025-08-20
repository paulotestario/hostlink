import sys
sys.path.append('c:\\hostlink')
from database import get_database

db = get_database()
bookings = db.get_user_bookings(1)

print(f'Bookings for user 1: {len(bookings) if bookings else 0}')

if bookings:
    for i, booking in enumerate(bookings[:5]):
        print(f'Booking {i+1}: ID={booking.get("id")}, Status={booking.get("status")}, Guest User ID={booking.get("guest_user_id")}')
else:
    print('No bookings found')