

# export SUPABASE_URL="https://qamgefqejxydheqabdxo.supabase.co"
# export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFhbWdlZnFlanh5ZGhlcWFiZHhvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY0NTE5NjAsImV4cCI6MjA4MjAyNzk2MH0.g2t5nlqUuOzu0z3adJFkvqNLwztljL3d3fE6SHOtx7I"


import os
import argparse
import time
from supabase import create_client


def main():
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    
    print(f"🔑 URL: {url[:30]}..." if url else "❌ URL not set")
    print(f"🔑 Key: {key[:30]}..." if key else "❌ Key not set")
    
    if not url or not key:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_KEY environment variables first.")

    supabase = create_client(url, key)
    
    parser = argparse.ArgumentParser(description="Room Management CLI")
    parser.add_argument("action", choices=["query", "join", "list", "leave", "watch"], help="Action to perform")
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
        
        # 检查用户是否在房间内
        user_in_room = supabase.table("pet_rooms").select("*").eq("room_id", args.room).eq("user_num", args.user).execute()
        
        if not user_in_room.data:
            print(f"❌ 用户 {args.user} 不在房间 {args.room} 中")
            return
        
        is_holder = user_in_room.data[0]["room_holder"]
        
        print(f"👀 开始监控房间 {args.room}...")
        print(f"{'👑 你是房主' if is_holder else '👤 你是普通成员'}")
        print("按 Ctrl+C 停止监控\n")
        
        try:
            while True:
                if is_holder:
                    # 房主：显示所有成员列表
                    room_members = supabase.table("pet_rooms").select("*").eq("room_id", args.room).execute()
                    
                    if not room_members.data:
                        print(f"❌ 房间 {args.room} 已不存在")
                        break
                    
                    print(f"📋 房间 {args.room} 成员列表 (共 {len(room_members.data)} 人):")
                    for member_row in room_members.data:
                        user_num = member_row["user_num"]
                        user_info = supabase.table("user_cur_pet").select("*").eq("user_num", user_num).execute()
                        if user_info.data:
                            pet = user_info.data[0]
                            marker = "👑" if member_row["room_holder"] else "👤"
                            print(f"  {marker} User {user_num}: {pet['pet_kind']} - {pet['pet_color']}")
                else:
                    # 普通成员：检查自己是否还在房间内
                    check_status = supabase.table("pet_rooms").select("*").eq("room_id", args.room).eq("user_num", args.user).execute()
                    
                    if not check_status.data:
                        print(f"❌ 房主已结束房间 {args.room}")
                        break
                    else:
                        print(f"✅ 仍在房间 {args.room} 中")
                
                print()  # 空行分隔
                time.sleep(3)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  停止监控")
    
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

