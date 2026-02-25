from system.models import UserProfile, Organization

# 1. 创建账户
user = UserProfile.objects.create_superuser(
    username='abc', 
    email='admin@example.com', 
    password='123456'
)

# 2. 设置你的业务逻辑角色
user.role = 'super_admin'


user.save()
print("✅ 超级管理员账户创建成功！")
exit()