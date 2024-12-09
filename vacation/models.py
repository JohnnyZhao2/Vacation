from django.db import models


class HolidayEvent(models.Model):
    # Primary key
    holidayevents_id = models.AutoField(primary_key=True)

    # 休假信息
    holidayevents_hname = models.CharField(max_length=20)  # 申请用户人姓名
    holidayevents_htype = models.CharField(max_length=20)  # 休假类型，年假，陪产假，病假，赡养老人假，婚假
    holidayevents_day = models.TextField()  # 休假日期
    holidayevents_remark = models.TextField()  # 休假说明
    holidayevents_ispermit = models.IntegerField()  # 审批状态: 1 = 待审批, 2 = 同意, 3 = 拒绝 4 = 已撤销
    holidayevents_approval_user = models.TextField()  # 审批人
    holidayevents_approval_opinion = models.TextField()  # 审批意见
    holidayevents_permittime = models.CharField(max_length=20, null=True, blank=True)  #审批时间
    holidayevents_usedDay = models.IntegerField()  # 休假天数
    holidayevents_addtime = models.DateTimeField()  # 提交时间
    runiuId = models.CharField(max_length=255, blank=True, verbose_name='孺牛单ID')
    taskId = models.CharField(max_length=255, blank=True, verbose_name='孺牛任务状态ID')

    class Meta:
        db_table = 'holiday_events'


class HolidayTimes(models.Model):
    # Primary key
    holidaytimes_id = models.AutoField(primary_key=True)
    holidaytimes_opname = models.CharField(max_length=11)  # 用户姓名
    holidaytimes_year = models.IntegerField()  # 休假年份
    holidaytimes_days = models.IntegerField()  # 可休天数
    holidaytimes_haddays = models.IntegerField()  # 已休天数
    holidaytimes_addtime = models.DateTimeField()  # 添加时间
    holidaytimes_workyear = models.IntegerField()  # 工作年份
    holidaytimes_cmbyear = models.IntegerField()  # Cmb年份

    class Meta:
        db_table = 'holiday_times'
