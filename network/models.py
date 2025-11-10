from django.db import models

class NumberSet(models.Model):
    mac_address = models.TextField()
    assigned_ip = models.TextField()
    dhcp_version = models.TextField()
    lease_time = models.TextField()
    lease_start = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

def __str__(self):
    return f"Set on {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

