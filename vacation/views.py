from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import HolidayEvent, HolidayTimes
from datetime import datetime
import time
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import requests

current_year = datetime.now().year

# Constants for status codes
STATUS_OK = 200
STATUS_CREATED = 201
STATUS_BAD_REQUEST = 400
STATUS_NOT_FOUND = 404
STATUS_METHOD_NOT_ALLOWED = 405


# Utility function for JSON responses
def json_response(data, status=STATUS_OK):
    return JsonResponse(data, status=status)

def validate_required_fields(data, required_fields):
    for field in required_fields:
        if not data.get(field):
            return json_response({'error': f'Missing required field: {field}'}, status=STATUS_BAD_REQUEST)
    return None

def get_token():
    url='http://127.0.0.1:8000/api/token/'
    headers = {'Content-Type': 'application/json'}
    data = {'username': 'admin', 'password': '123456'}
    response = requests.post(url, headers=headers, json=data)
    return response.json()['access']


@csrf_exempt
@require_http_methods(["GET"])
def get_vacation_list(request):
    vacation_list = HolidayEvent.objects.all().order_by('-holidayevents_addtime')
    return json_response({'vacation_list': list(vacation_list.values())})

@csrf_exempt
@require_http_methods(["GET"])
def vacation_quota_list(request):
    vacation_quota = HolidayTimes.objects.all()
    return json_response({'vacation_quota': list(vacation_quota.values())})

@csrf_exempt
@require_http_methods(["POST"])
def submit_vacation(request):
    data = json.loads(request.body)
    required_fields = ['username', 'leave_type', 'leave_day', 'reason']
    validation_error = validate_required_fields(data, required_fields)
    if validation_error:
        return validation_error

    username = data.get('username')
    leave_type = data.get('leave_type')
    leave_day = data.get('leave_day')  # format: 2024-04-01,2024-04-02,2024-04-03
    reason = data.get('reason')

    
    used_days = len(leave_day.split(','))  # Number of days of leave used

    if leave_type == '年假':
        holiday_times = get_object_or_404(HolidayTimes, holidaytimes_opname=username, holidaytimes_year=current_year)  # User's holiday_times data for the current year
        if holiday_times.holidaytimes_days < used_days:
            return json_response({'error': 'User has already used all their annual leave for the year'}, status=STATUS_BAD_REQUEST)

    # create a vacation event
    vacation_event = HolidayEvent(
        holidayevents_hname=username,
        holidayevents_htype=leave_type,
        holidayevents_day=leave_day,
        holidayevents_remark=reason,
        holidayevents_usedDay=used_days,
        holidayevents_ispermit=1,
        holidayevents_addtime=datetime.now()
    )
    vacation_event.save()
    return json_response({'message': 'Vacation event created successfully'}, status=STATUS_CREATED)

@csrf_exempt
@require_http_methods(["POST"])
def revoke_vacation(request):
    data = json.loads(request.body)
    id = data.get('vacation_id')
    if not id:
        return json_response({'error': 'Missing required field: vacation_id'}, status=STATUS_BAD_REQUEST)

    vacation_event = get_object_or_404(HolidayEvent, holidayevents_id=id)
    if vacation_event.holidayevents_ispermit != 1:
        return json_response({'error': 'Only pending vacation events can be revoked'}, status=STATUS_BAD_REQUEST)

    vacation_event.holidayevents_ispermit = 4  # 4: revoked
    vacation_event.save()
    return json_response({'message': 'Vacation event revoked successfully'}, status=STATUS_OK)

@csrf_exempt
@require_http_methods(["POST"])
def delete_vacation(request):
    data = json.loads(request.body)
    id = data.get('vacation_id')
    if not id:
        return json_response({'error': 'Missing required field: vacation_id'}, status=STATUS_BAD_REQUEST)
    vacation_event = get_object_or_404(HolidayEvent, holidayevents_id=id)
    vacation_event.delete()
    return json_response({'message': 'Vacation event deleted successfully'}, status=STATUS_OK)

@csrf_exempt
@require_http_methods(["GET"])
def get_user_vacation_info(request):
    username = request.GET.get('username')
    if not username:
        return json_response({'error': 'Missing username parameter'}, status=STATUS_BAD_REQUEST)
    vacation_info = HolidayEvent.objects.filter(holidayevents_hname=username).order_by('-holidayevents_addtime')
    return json_response({'vacation_info': list(vacation_info.values())})

@csrf_exempt
@require_http_methods(["POST"])
def approve_vacation(request):
    try:
        data = json.loads(request.body)

        # Check for missing fields
        required_fields = ['id', 'opinion', 'ispermit']
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return validation_error
        
        id = data.get('id')
        approver = data.get('approver')
        opinion = data.get('opinion')
        ispermit = data.get('ispermit')  # 1: pending, 2: approved, 3: rejected
        vacation_event = get_object_or_404(HolidayEvent, holidayevents_id=id)
        if vacation_event.holidayevents_ispermit != 1:
            return json_response({'error': 'Vacation event is not pending'}, status=STATUS_BAD_REQUEST)

        vacation_event.holidayevents_approval_user = approver
        vacation_event.holidayevents_approval_opinion = opinion
        vacation_event.holidayevents_ispermit = ispermit
        vacation_event.holidayevents_permittime = str(int(time.time())) # Changed to DateTimeField

        # Update holiday_times if ispermit == 2 (approved)
        if ispermit == 2 and vacation_event.holidayevents_htype == '年假':
            holiday_times = get_object_or_404(HolidayTimes, holidaytimes_opname=vacation_event.holidayevents_hname, holidaytimes_year=current_year)
            holiday_times.holidaytimes_days -= vacation_event.holidayevents_usedDay
            holiday_times.holidaytimes_haddays += vacation_event.holidayevents_usedDay
            holiday_times.save()

        vacation_event.save()

        if ispermit == 2:
            return json_response({'message': 'Vacation event approved successfully'}, status=STATUS_OK)
        elif ispermit == 3:
            return json_response({'message': 'Vacation event rejected successfully'}, status=STATUS_OK)
        else:
            return json_response({'error': 'Invalid ispermit value'}, status=STATUS_BAD_REQUEST)
    except json.JSONDecodeError:
        return json_response({'error': 'Invalid JSON'}, status=STATUS_BAD_REQUEST)

@csrf_exempt
@require_http_methods(["GET"])
def get_approve_vacation_list(request):
    vacation_list = HolidayEvent.objects.filter(holidayevents_ispermit=1).order_by('-holidayevents_addtime')
    return json_response({'vacation_list': list(vacation_list.values())})

@csrf_exempt
@require_http_methods(["POST"])
def create_vacation_times(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        year = data.get('year')
        days = data.get('days')
        haddays = data.get('haddays')  # Default to 0 if not provided
        workyear = data.get('workyear')
        cmb_year = data.get('cmb_year')

        # Check for missing fields
        required_fields = ['username', 'year', 'days', 'workyear', 'cmb_year']
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return validation_error

        vacation_times = HolidayTimes(
            holidaytimes_opname=username,
            holidaytimes_year=year,
            holidaytimes_days=days,
            holidaytimes_haddays=haddays,
            holidaytimes_workyear=workyear,
            holidaytimes_cmbyear=cmb_year,
            holidaytimes_addtime=datetime.now()
        )
        vacation_times.save()
        return json_response({'message': 'Vacation times added successfully'}, status=STATUS_CREATED)
    except json.JSONDecodeError:
        return json_response({'error': 'Invalid JSON'}, status=STATUS_BAD_REQUEST)

@csrf_exempt
@require_http_methods(["POST"])
def update_vacation_times(request):
    try:
        data = json.loads(request.body)
        id = data.get('id')
        if not id:
            return json_response({'error': 'Missing required field: id'}, status=STATUS_BAD_REQUEST)

        vacation_times = get_object_or_404(HolidayTimes, holidaytimes_id=id)

        field_mapping = {
            'year': 'holidaytimes_year',
            'available_days': 'holidaytimes_days',
            'used_days': 'holidaytimes_haddays',
            'work_year': 'holidaytimes_workyear',
            'cmb_year': 'holidaytimes_cmbyear'
        }

        # Update only the fields that are provided and valid
        updated_fields = {}
        for custom_field,model_field in field_mapping.items():
            if custom_field in data:
                setattr(vacation_times, model_field, data[custom_field])
                updated_fields[model_field] = data[custom_field]

        if not updated_fields:
            return json_response({'error': 'No valid fields provided for update'}, status=STATUS_BAD_REQUEST)

        vacation_times.save()

        return json_response({'message': 'Vacation times updated successfully', 'updated_fields': updated_fields}, status=STATUS_OK)
    except json.JSONDecodeError:
        return json_response({'error': 'Invalid JSON'}, status=STATUS_BAD_REQUEST)

@csrf_exempt
@require_http_methods(["POST"])
def delete_vacation_times(request):
    data = json.loads(request.body)
    id = data.get('id')
    opname = data.get('opname')
    vacation_times = get_object_or_404(HolidayTimes, holidaytimes_id=id)
    vacation_times.delete()
    return json_response({'message': 'Vacation times deleted successfully'}, status=STATUS_OK)

@csrf_exempt
@require_http_methods(["GET"])
def get_user_holiday_info(request):
    username = request.GET.get('opname')
    if not username:
        return json_response({'error': 'Missing opname parameter'}, status=STATUS_BAD_REQUEST)
    holiday_info = HolidayTimes.objects.filter(holidaytimes_opname=username).order_by('-holidaytimes_addtime')
    return json_response({'holiday_info': list(holiday_info.values())})


