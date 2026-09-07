import ast,operator
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
router=Router(name="tools")
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Pow:operator.pow,ast.Mod:operator.mod,ast.USub:operator.neg,ast.UAdd:operator.pos}
def calculate(expr:str)->float:
 if len(expr)>200: raise ValueError("عبارت طولانی است")
 def walk(n):
  if isinstance(n,ast.Expression): return walk(n.body)
  if isinstance(n,ast.Constant) and type(n.value) in {int,float}: return n.value
  if isinstance(n,ast.BinOp) and type(n.op) in OPS:
   a,b=walk(n.left),walk(n.right)
   if type(n.op) is ast.Pow and abs(b)>10: raise ValueError("توان بیش از حد")
   return OPS[type(n.op)](a,b)
  if isinstance(n,ast.UnaryOp) and type(n.op) in OPS:return OPS[type(n.op)](walk(n.operand))
  raise ValueError("عملگر غیرمجاز")
 result=walk(ast.parse(expr,mode="eval"))
 if abs(result)>1e100: raise ValueError("خروجی بیش از حد بزرگ")
 return result
@router.message(Command("calc"))
async def calc(message:Message)->None:
 expr=(message.text or "").partition(" ")[2].replace("^","**")
 try: await message.answer(f"<code>{calculate(expr):g}</code>")
 except Exception as e: await message.answer(f"عبارت نامعتبر: {e}")
@router.message(Command("percent"))
async def percent(message:Message)->None:
 try:
  _,p,n=(message.text or "").split(); await message.answer(f"{float(p)*float(n)/100:g}")
 except (ValueError,IndexError): await message.answer("/percent 20 150")
