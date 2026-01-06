

# export SUPABASE_URL="https://qamgefqejxydheqabdxo.supabase.co"
# export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFhbWdlZnFlanh5ZGhlcWFiZHhvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY0NTE5NjAsImV4cCI6MjA4MjAyNzk2MH0.g2t5nlqUuOzu0z3adJFkvqNLwztljL3d3fE6SHOtx7I"


import os
import argparse
import asyncio
from datetime import datetime
from supabase import create_client, acreate_client


async def watch_room_async(url: str, key: str, room_id: int, user_num: int):
    """异步监控房间"""
    # 先用同步客户端检查用户状态
    supabase_sync = create_client(url, key)
    user_in_room = supabase_sync.table("pet_rooms").select("*").eq("room_id", room_id).eq("user_num", user_num).execute()
    
    if not user_in_room.data:
        print(f"❌ 用户 {user_num} 不在房间 {room_id} 中")
        return
    
    is_holder = user_in_room.data[0]["room_holder"]
    
    print(f"👀 开始监控房间 {room_id}...")
    print(f"{'👑 你是房主' if is_holder else '👤 你是普通成员'}")
    if is_holder:
        print("输入 'leave' 并回车可退出房间")
    print("按 Ctrl+C 停止监控\n")
    
    # 创建异步客户端
    supabase = await acreate_client(url, key)
    
    should_exit = False
    
    async def display_room_members():
        """显示房间成员列表"""
        room_members = await supabase.table("pet_rooms").select("*").eq("room_id", room_id).execute()
        
        if not room_members.data:
            return False
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}]")
        for member_row in room_members.data:
            user_num_m = member_row["user_num"]
            user_info = await supabase.table("user_cur_pet").select("*").eq("user_num", user_num_m).execute()
            if user_info.data:
                pet = user_info.data[0]
                marker = "👑" if member_row["room_holder"] else "👤"
                print(f"  {marker} User {user_num_m}: {pet['pet_kind']} - {pet['pet_color']}")
        print()
        return True
    
    async def check_owner_input():
        """异步检查房主输入"""
        nonlocal should_exit
        loop = asyncio.get_event_loop()
        while not should_exit:
            try:
                user_input = await loop.run_in_executor(None, input)
                if user_input.strip().lower() == 'leave':
                    should_exit = True
                    break
            except:
                break
    
    if is_holder:
        # 房主：使用 Realtime 监听数据库变化
        # 先显示初始成员列表
        if not await display_room_members():
            print(f"❌ 房间 {room_id} 已不存在")
            return
        
        # 创建 channel 并订阅变化
        channel = supabase.channel(f'room_{room_id}')
        
        async def handle_changes(payload):
            # print(f"🔍 DEBUG: 收到完整事件 {payload}")
            
            if should_exit:
                return
            
            # 正确解析 Supabase Realtime payload 结构
            data = payload.get('data', {})
            event_type = data.get('type')
            new_record = data.get('record', {})
            old_record = data.get('old_record', {})  # DELETE 时可能有
            
            # print(f"🔍 解析后: event_type={event_type}, new_record={new_record}, old_record={old_record}")
            
            # 只处理当前房间的变化
            changed_room_id = new_record.get('room_id') or old_record.get('room_id')
            # print(f"🔍 房间ID={changed_room_id}, 目标房间={room_id}")
            
            if changed_room_id == room_id:
                if event_type == 'INSERT':
                    print(f"🔔 新成员加入!")
                elif event_type == 'DELETE':
                    print(f"🔔 成员离开!")
                
                # 重新显示成员列表
                if not await display_room_members():
                    print(f"❌ 房间 {room_id} 已不存在")
                    print(f"❌ 房间 {room_id} 已不存在")
        
        channel.on_postgres_changes(
            event='*',
            schema='public',
            table='pet_rooms',
            callback=lambda payload: asyncio.create_task(handle_changes(payload))
        )
        
        print(f"🔍 正在订阅...")
        await channel.subscribe()
        print(f"✅ 订阅成功，等待变化...")
        
        # 启动输入监听任务
        input_task = asyncio.create_task(check_owner_input())
        
        try:
            # 等待退出信号
            while not should_exit:
                await asyncio.sleep(0.5)
            
            # 退出时删除房间
            print(f"\n🏠 房主退出，删除房间 {room_id}...")
            await supabase.table("pet_rooms").delete().eq("room_id", room_id).execute()
            print(f"✅ 房间 {room_id} 已删除")
            
        except KeyboardInterrupt:
            print("\n\n⏹️  停止监控")
            print("提示: 房间仍然存在，使用 'leave' 命令删除房间")
        finally:
            await channel.unsubscribe()
    
    else:
        # 普通成员：使用 Realtime 监听房主离开（房间删除）
        channel = supabase.channel(f'member_room_{room_id}_{user_num}')
        
        room_exists = True
        
        async def handle_member_changes(payload):
            nonlocal room_exists
            
            if not room_exists:
                return
            
            # 正确解析 Supabase Realtime payload 结构
            data = payload.get('data', {})
            event_type = data.get('type')
            old_record = data.get('old_record', {})
            new_record = data.get('record', {})
            
            # 获取被删除或变化的房间ID和用户ID
            changed_room_id = old_record.get('room_id') or new_record.get('room_id')
            deleted_user_num = old_record.get('user_num')
            
            # 只处理当前房间的DELETE事件
            if changed_room_id == room_id and event_type == 'DELETE':
                # 如果删除的是自己的记录，说明房间已关闭（房主删除了整个房间）
                if deleted_user_num == user_num:
                    print(f"\n🔔 房主已离开，房间 {room_id} 已关闭")
                    room_exists = False
        
        channel.on_postgres_changes(
            event='DELETE',
            schema='public',
            table='pet_rooms',
            callback=lambda payload: asyncio.create_task(handle_member_changes(payload))
        )
        
        print(f"🔍 正在订阅房间 {room_id} 的变化...")
        await channel.subscribe()
        print(f"✅ 订阅成功，等待房主动态...")
        
        try:
            # 等待房间关闭
            while room_exists:
                await asyncio.sleep(0.5)
            
            print(f"👋 已自动退出房间")
                
        except KeyboardInterrupt:
            print("\n\n⏹️  停止监控")
        finally:
            await channel.unsubscribe()


def main():
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    
    print(f"🔑 URL: {url[:30]}..." if url else "❌ URL not set")
    print(f"🔑 Key: {key[:30]}..." if key else "❌ Key not set")
    
    if not url or not key:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_KEY environment variables first.")

    supabase = create_client(url, key)
    
    parser = argparse.ArgumentParser(description="Room Management CLI")
    parser.add_argument("action", choices=["query", "join", "list", "leave", "watch", "connect"], help="Action to perform")
    parser.add_argument("--user", type=int, help="User number")
    parser.add_argument("--room", type=int, help="Room ID")
    
    args = parser.parse_args()
    
    if args.action == "query":
        if not args.user:
            print("❌ 查询用户需要 --user 参数")
            return
        # 查询用户宠物信息
        print(f"🔍 查询用户 {args.user} 的宠物信息...")
        result = supabase.table("user_cur_pet").select("*").eq("user_num", args.user).execute()
        
        if result.data:
            user_info = result.data[0]
            print(f"\n👤 用户 {user_info['user_num']} 的宠物信息:")
            print(f"   宠物种类: {user_info['pet_kind']}")
            print(f"   宠物颜色: {user_info['pet_color']}")
        else:
            print(f"\n❌ 找不到用户 {args.user} 的信息")
    
    elif args.action == "list":
        if not args.room:
            print("❌ 查看房间成员需要 --room 参数")
            return
        
        print(f"🔍 查询房间 {args.room} 的成员...")
        room_members = supabase.table("pet_rooms").select("*").eq("room_id", args.room).execute()
        
        if not room_members.data:
            print(f"\n❌ 房间 {args.room} 不存在或没有成员")
            return
        
        print(f"\n📋 房间 {args.room} 成员列表 (共 {len(room_members.data)} 人):")
        for member_row in room_members.data:
            user_num = member_row["user_num"]
            user_info = supabase.table("user_cur_pet").select("*").eq("user_num", user_num).execute()
            if user_info.data:
                pet = user_info.data[0]
                marker = "👑" if member_row["room_holder"] else "👤"
                print(f"  {marker} User {user_num}: {pet['pet_kind']} - {pet['pet_color']}")
    
    elif args.action == "leave":
        if not args.user or not args.room:
            print("❌ 退出房间需要 --user 和 --room 参数")
            return
        
        # 检查用户是否在房间内
        print(f"🔍 检查用户 {args.user} 是否在房间 {args.room} 中...")
        user_in_room = supabase.table("pet_rooms").select("*").eq("room_id", args.room).eq("user_num", args.user).execute()
        
        if not user_in_room.data:
            print(f"❌ 用户 {args.user} 不在房间 {args.room} 中")
            return
        
        is_holder = user_in_room.data[0]["room_holder"]
        
        if is_holder:
            # 房主退出，删除房间所有成员
            print(f"👑 你是房主，退出将删除整个房间 {args.room}...")
            supabase.table("pet_rooms").delete().eq("room_id", args.room).execute()
            print(f"✅ 房间 {args.room} 已删除")
        else:
            # 普通成员退出，只删除自己的记录
            print(f"👤 退出房间 {args.room}...")
            supabase.table("pet_rooms").delete().eq("room_id", args.room).eq("user_num", args.user).execute()
            print(f"✅ 已退出房间 {args.room}")
    
    elif args.action == "watch":
        if not args.user or not args.room:
            print("❌ 监控房间需要 --user 和 --room 参数")
            return
        
        # 使用 asyncio 运行 watch
        asyncio.run(watch_room_async(url, key, args.room, args.user))
    
    elif args.action == "connect":
        if not args.user or not args.room:
            print("❌ 连接房间需要 --user 和 --room 参数")
            return
        
        # 先查询用户宠物信息
        user_result = supabase.table("user_cur_pet").select("*").eq("user_num", args.user).execute()
        if not user_result.data:
            print(f"❌ 找不到用户 {args.user} 的宠物信息，请先确保用户存在")
            return
        
        # 检查房间是否存在
        print(f"🔍 检查房间 {args.room} 是否存在...")
        room_check = supabase.table("pet_rooms").select("*").eq("room_id", args.room).execute()
        
        if not room_check.data:
            # 房间不存在，创建新房间，此用户为房主
            print(f"✅ 房间 {args.room} 不存在，创建新房间...")
            supabase.table("pet_rooms").insert({
                "room_id": args.room,
                "user_num": args.user,
                "room_holder": True
            }).execute()
            print(f"👑 你是房间 {args.room} 的房主")
        else:
            # 房间已存在，检查用户是否已在房间内
            existing_members = [row["user_num"] for row in room_check.data]
            if args.user in existing_members:
                print(f"⚠️  你已经在房间 {args.room} 中了")
            else:
                # 加入房间，不是房主
                print(f"✅ 加入现有房间 {args.room}...")
                supabase.table("pet_rooms").insert({
                    "room_id": args.room,
                    "user_num": args.user,
                    "room_holder": False
                }).execute()
                print(f"👤 成功加入房间 {args.room}")
        
        # 显示房间成员列表
        print(f"\n📋 房间 {args.room} 成员列表:")
        all_members = supabase.table("pet_rooms").select("*").eq("room_id", args.room).execute()
        for member_row in all_members.data:
            user_num = member_row["user_num"]
            user_info = supabase.table("user_cur_pet").select("*").eq("user_num", user_num).execute()
            if user_info.data:
                pet = user_info.data[0]
                marker = "👑" if member_row["room_holder"] else "👤"
                print(f"  {marker} User {user_num}: {pet['pet_kind']} - {pet['pet_color']}")
        
        print()
        # 自动开始监听
        asyncio.run(watch_room_async(url, key, args.room, args.user))
    
    elif args.action == "join":
        if not args.user or not args.room:
            print("❌ 加入房间需要 --user 和 --room 参数")
            return
        
        # 先查询用户宠物信息
        user_result = supabase.table("user_cur_pet").select("*").eq("user_num", args.user).execute()
        if not user_result.data:
            print(f"❌ 找不到用户 {args.user} 的宠物信息，请先确保用户存在")
            return
        
        # 检查房间是否存在
        print(f"🔍 检查房间 {args.room} 是否存在...")
        room_check = supabase.table("pet_rooms").select("*").eq("room_id", args.room).execute()
        
        is_holder = False
        if not room_check.data:
            # 房间不存在，创建新房间，此用户为房主
            print(f"✅ 房间 {args.room} 不存在，创建新房间...")
            supabase.table("pet_rooms").insert({
                "room_id": args.room,
                "user_num": args.user,
                "room_holder": True
            }).execute()
            is_holder = True
            print(f"👑 你是房间 {args.room} 的房主")
        else:
            # 房间已存在，检查用户是否已在房间内
            existing_members = [row["user_num"] for row in room_check.data]
            if args.user in existing_members:
                print(f"⚠️  你已经在房间 {args.room} 中了")
                return
            
            # 加入房间，不是房主
            print(f"✅ 加入现有房间 {args.room}...")
            supabase.table("pet_rooms").insert({
                "room_id": args.room,
                "user_num": args.user,
                "room_holder": False
            }).execute()
            print(f"👤 成功加入房间 {args.room}")
        
        # 显示房间成员列表
        print(f"\n📋 房间 {args.room} 成员列表:")
        all_members = supabase.table("pet_rooms").select("*").eq("room_id", args.room).execute()
        for member_row in all_members.data:
            user_num = member_row["user_num"]
            user_info = supabase.table("user_cur_pet").select("*").eq("user_num", user_num).execute()
            if user_info.data:
                pet = user_info.data[0]
                marker = "👑" if member_row["room_holder"] else "👤"
                print(f"  {marker} User {user_num}: {pet['pet_kind']} - {pet['pet_color']}")


if __name__ == "__main__":
    main()


# ============= API for GUI Integration =============

async def watch_room_with_callback(url: str, key: str, room_id: int, user_num: int, callback, stop_event):
    """
    异步监控房间，通过callback发送事件到GUI
    callback(event_type, data) where:
        - event_type: 'connected', 'member_joined', 'member_left', 'room_closed', 'error', 'members_list'
        - data: dict with relevant information
    stop_event: threading.Event to signal when to stop
    """
    try:
        # 先用同步客户端检查用户状态和加入房间
        supabase_sync = create_client(url, key)
        
        # 检查用户是否存在
        user_result = supabase_sync.table("user_cur_pet").select("*").eq("user_num", user_num).execute()
        if not user_result.data:
            callback('error', {'message': f'用户 {user_num} 不存在'})
            return
        
        # 检查房间是否存在
        room_check = supabase_sync.table("pet_rooms").select("*").eq("room_id", room_id).execute()
        
        is_holder = False
        if not room_check.data:
            # 房间不存在，创建新房间
            supabase_sync.table("pet_rooms").insert({
                "room_id": room_id,
                "user_num": user_num,
                "room_holder": True
            }).execute()
            is_holder = True
            callback('connected', {'room_id': room_id, 'user_id': user_num, 'is_holder': True})
        else:
            # 房间已存在，检查用户是否已在房间内
            existing_members = [row["user_num"] for row in room_check.data]
            if user_num in existing_members:
                # 已在房间内，直接监控
                user_in_room = [row for row in room_check.data if row["user_num"] == user_num][0]
                is_holder = user_in_room["room_holder"]
            else:
                # 加入房间
                supabase_sync.table("pet_rooms").insert({
                    "room_id": room_id,
                    "user_num": user_num,
                    "room_holder": False
                }).execute()
                is_holder = False
            callback('connected', {'room_id': room_id, 'user_id': user_num, 'is_holder': is_holder})
        
        # 创建异步客户端
        supabase = await acreate_client(url, key)
        
        async def get_room_members():
            """获取房间成员列表"""
            room_members = await supabase.table("pet_rooms").select("*").eq("room_id", room_id).execute()
            if not room_members.data:
                return None
            
            members = []
            for member_row in room_members.data:
                user_num_m = member_row["user_num"]
                user_info = await supabase.table("user_cur_pet").select("*").eq("user_num", user_num_m).execute()
                if user_info.data:
                    pet = user_info.data[0]
                    members.append({
                        'user_id': user_num_m,
                        'pet_kind': pet['pet_kind'],
                        'pet_color': pet['pet_color'],
                        'is_holder': member_row['room_holder']
                    })
            return members
        
        # 发送初始成员列表
        members = await get_room_members()
        if members is None:
            callback('error', {'message': f'房间 {room_id} 已不存在'})
            return
        callback('members_list', {'members': members})
        
        if is_holder:
            # 房主：监听所有变化
            channel = supabase.channel(f'room_{room_id}')
            
            async def handle_changes(payload):
                if stop_event.is_set():
                    return
                
                data = payload.get('data', {})
                event_type = data.get('type')
                new_record = data.get('record', {})
                old_record = data.get('old_record', {})
                
                changed_room_id = new_record.get('room_id') or old_record.get('room_id')
                
                if changed_room_id == room_id:
                    if event_type == 'INSERT':
                        callback('member_joined', {'user_id': new_record.get('user_num')})
                    elif event_type == 'DELETE':
                        callback('member_left', {'user_id': old_record.get('user_num')})
                    
                    # 更新成员列表
                    members = await get_room_members()
                    if members is None:
                        callback('room_closed', {})
                    else:
                        callback('members_list', {'members': members})
            
            channel.on_postgres_changes(
                event='*',
                schema='public',
                table='pet_rooms',
                callback=lambda payload: asyncio.create_task(handle_changes(payload))
            )
            
            await channel.subscribe()
            
            try:
                # 等待停止信号
                while not stop_event.is_set():
                    await asyncio.sleep(0.5)
                
                # 房主退出，删除房间
                await supabase.table("pet_rooms").delete().eq("room_id", room_id).execute()
                callback('room_closed', {'message': '房主退出，房间已删除'})
                
            finally:
                await channel.unsubscribe()
        
        else:
            # 普通成员：只监听房间删除
            channel = supabase.channel(f'member_room_{room_id}_{user_num}')
            
            room_exists = True
            
            async def handle_member_changes(payload):
                nonlocal room_exists
                
                if not room_exists or stop_event.is_set():
                    return
                
                data = payload.get('data', {})
                event_type = data.get('type')
                old_record = data.get('old_record', {})
                new_record = data.get('record', {})
                
                changed_room_id = old_record.get('room_id') or new_record.get('room_id')
                deleted_user_num = old_record.get('user_num')
                
                if changed_room_id == room_id and event_type == 'DELETE':
                    if deleted_user_num == user_num:
                        callback('room_closed', {'message': '房主已关闭房间'})
                        room_exists = False
            
            channel.on_postgres_changes(
                event='DELETE',
                schema='public',
                table='pet_rooms',
                callback=lambda payload: asyncio.create_task(handle_member_changes(payload))
            )
            
            await channel.subscribe()
            
            try:
                while room_exists and not stop_event.is_set():
                    await asyncio.sleep(0.5)
                
                # 普通成员退出时，删除自己的记录
                if not stop_event.is_set():
                    # 如果是因为房间关闭而退出，不需要删除（已被房主删除）
                    pass
                else:
                    # 主动退出，删除自己的记录
                    await supabase.table("pet_rooms").delete().eq("room_id", room_id).eq("user_num", user_num).execute()
                    callback('room_closed', {'message': '已退出房间'})
                    
            finally:
                await channel.unsubscribe()
    
    except Exception as e:
        callback('error', {'message': str(e)})


def start_room_connection(url: str, key: str, room_id: int, user_id: int, callback, stop_event):
    """
    在新的事件循环中启动房间连接（在单独的线程中调用）
    callback: 接收事件的回调函数 callback(event_type, data)
    stop_event: threading.Event 用于停止连接
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            watch_room_with_callback(url, key, room_id, user_id, callback, stop_event)
        )
    finally:
        loop.close()
