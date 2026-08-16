from flask import Flask,request,redirect
import os
from datetime import datetime

app=Flask(__name__)

DATA_FILE='data.txt'

def load_data():
	"""从 data.txt 读取账目，返回一个列表，每条记录是一个字典，增加兼容模式（没有日期的数据自动补上'未知日期'）"""
	book=[]
	if os.path.exists(DATA_FILE):
		with open(DATA_FILE,'r',encoding='utf-8') as f:
			for line in f:
				line=line.strip()
				if line:
					parts=line.split('|')
					#兼容处理：如果只有名称和日期，自动补上'未知日期'
					if len(parts)==2:
						name,amount=parts[0],float(parts[1])
						date="未知日期"
					elif len(parts)>=3:
					   name,amount,date=parts[0],float(parts[1]),parts[2]
					else:
						continue #格式不对就跳过
					book.append({"name":parts[0],"amount":float(parts[1]),"date": date})
	return book
	
def save_data(book):
	"""把列表里的所有账目写入 data.txt（覆盖写入）"""
	with open(DATA_FILE, 'w', encoding='utf-8') as f:
		for item in book:
			f.write(f"{item['name']}|{item['amount']}|{item['date']}\n")

@app.route('/')
def show_ledger():
	book=load_data()
	
	total=0
	for item in book:
		total=total+item["amount"]
		
	html = """
	<!DOCTYPE html>
	<html>
	<head>
		<title>我的记账本</title>
		<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
		<style>
			body { background: #f8f9fa; margin-top: 50px; }
			.container { max-width: 800px; }
		</style>
	</head>
	<body>
		<div class="container">
			<div class="card shadow-sm">
				<div class="card-header bg-primary text-white">
					<h3 class="mb-0">📒 我的记账本</h3>
				</div>
				<div class="card-body">
					<div class="mb-3">
						<a href="/add" class="btn btn-success">➕ 添加新账目</a>
					</div>
					<table class="table table-striped table-hover">
						<thead class="table-dark">
							<tr><th>名称</th><th>金额</th><th>日期</th><th>操作</th></tr>
						</thead>
						<tbody>
	"""
	
	if not book:
		html += '<tr><td colspan="4" class="text-center text-muted">📭 暂无账目，快去添加吧！</td></tr>'
	else:
		for idx, item in enumerate(book):  # [新增] enumerate 可以拿到索引号（用于删除）
			html += f"""
				<tr>
					<td>{item['name']}</td>
					<td>¥ {item['amount']:.2f}</td>
					<td>{item['date']}</td>
					<td>
						<a href="/edit/{idx}" class="btn btn-warning btn-sm">✏️ 编辑</a>
						<a href="/delete/{idx}" class="btn btn-danger btn-sm" onclick="return confirm('确定要删除这条记录吗？')">删除</a>
					</td>
				</tr>
			"""
	
	html += f"""
						</tbody>
						<tfoot class="table-warning">
							<tr><td colspan="3"><strong>总计</strong></td><td><strong>¥ {total:.2f}</strong></td></tr>
						</tfoot>
					</table>
				</div>
			</div>
		</div>
	</body>
	</html>
	"""
	return html

@app.route('/add', methods=['GET', 'POST'])
def add_record():
	if request.method == 'POST':
		name = request.form.get('name')
		amount = request.form.get('amount')
		
		# [新增] 更完善的报错提示
		if not name or not amount:
			return "<h3>⚠️ 名称和金额都不能为空！<a href='/add'>返回重试</a></h3>"
		try:
			amount_float = float(amount)
			if amount_float <= 0:
				return "<h3>⚠️ 金额必须大于 0！<a href='/add'>返回重试</a></h3>"
		except ValueError:
			return "<h3>⚠️ 金额格式不正确（请输入数字）！<a href='/add'>返回重试</a></h3>"
		
		# [新增] 获取当前日期并格式化
		today = datetime.now().strftime("%Y-%m-%d %H:%M")
		
		book = load_data()
		book.append({"name": name, "amount": amount_float, "date": today})
		save_data(book)
		return redirect('/')
	
	# GET 请求显示表单（同样用 Bootstrap 美化）
	html = """
	<!DOCTYPE html>
	<html>
	<head>
		<title>添加账目</title>
		<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
		<style>body { background: #f8f9fa; margin-top: 50px; } .container { max-width: 500px; }</style>
	</head>
	<body>
		<div class="container">
			<div class="card">
				<div class="card-header bg-success text-white"><h3>➕ 添加新账目</h3></div>
				<div class="card-body">
					<form method="POST">
						<div class="mb-3">
							<label>名称</label>
							<input type="text" name="name" class="form-control" placeholder="例如：买书" required>
						</div>
						<div class="mb-3">
							<label>金额</label>
							<input type="number" step="0.01" name="amount" class="form-control" placeholder="例如：39.9" required>
						</div>
						<button type="submit" class="btn btn-primary w-100">✅ 保存</button>
					</form>
					<br>
					<a href="/" class="btn btn-secondary w-100">← 返回首页</a>
				</div>
			</div>
		</div>
	</body>
	</html>
	"""
	return html

#删除功能
@app.route('/delete/<int:idx>')
def delete_record(idx):
	book = load_data()
	# 检查索引是否有效（防止有人手动输入越界的数字）
	if 0 <= idx < len(book):
		removed = book.pop(idx)  # pop 会移除并返回被删的元素
		save_data(book)
		print(f"已删除：{removed['name']}")  # 在终端显示删除日志
	else:
		return "<h3>⚠️ 记录不存在！<a href='/'>返回首页</a></h3>"
	return redirect('/')

#编辑功能
@app.route('/edit/<int:idx>', methods=['GET', 'POST'])
def edit_record(idx):
	book = load_data()
	
	# 检查索引是否有效
	if idx < 0 or idx >= len(book):
		return "<h3>⚠️ 记录不存在！<a href='/'>返回首页</a></h3>"
	
	# 情况1：用户提交了修改表单（POST请求）
	if request.method == 'POST':
		name = request.form.get('name')
		amount = request.form.get('amount')
		
		# 简单校验
		if not name or not amount:
			return "<h3>⚠️ 名称和金额不能为空！<a href='/edit/" + str(idx) + "'>返回重试</a></h3>"
		try:
			amount_float = float(amount)
			if amount_float <= 0:
				return "<h3>⚠️ 金额必须大于 0！<a href='/edit/" + str(idx) + "'>返回重试</a></h3>"
		except ValueError:
			return "<h3>⚠️ 金额格式不正确！<a href='/edit/" + str(idx) + "'>返回重试</a></h3>"
		
		# 核心：更新列表中的数据（保留原来的日期，或者更新为“编辑时间”）
		from datetime import datetime
		book[idx]['name'] = name
		book[idx]['amount'] = amount_float
		# 为了让改动可见，我们把日期改为“编辑于 当前时间”
		book[idx]['date'] = datetime.now().strftime("%Y-%m-%d %H:%M") + " (已编辑)"
		
		save_data(book)
		return redirect('/')
	
	# 情况2：用户点击了“编辑”按钮，看到了编辑页面（GET请求）
	record = book[idx]
	# 渲染编辑页面，注意 input 框的 value 里已经填好了旧数据
	html = f"""
	<!DOCTYPE html>
	<html>
	<head>
		<title>编辑账目</title>
		<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
		<style>body {{ background: #f8f9fa; margin-top: 50px; }} .container {{ max-width: 500px; }}</style>
	</head>
	<body>
		<div class="container">
			<div class="card">
				<div class="card-header bg-warning text-dark"><h3>✏️ 编辑账目</h3></div>
				<div class="card-body">
					<form method="POST">
						<div class="mb-3">
							<label>名称</label>
							<input type="text" name="name" class="form-control" value="{record['name']}" required>
						</div>
						<div class="mb-3">
							<label>金额</label>
							<input type="number" step="0.01" name="amount" class="form-control" value="{record['amount']:.2f}" required>
						</div>
						<button type="submit" class="btn btn-warning w-100">💾 更新</button>
					</form>
					<br>
					<a href="/" class="btn btn-secondary w-100">← 返回首页</a>
				</div>
			</div>
		</div>
	</body>
	</html>
	"""
	return html

		
if __name__=='__main__':
	app.run(debug=True)
