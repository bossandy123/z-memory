import asyncio
from sqlalchemy import text
from app.database.models import async_session


async def migrate_add_rl_fields():
    """
    添加 RL 飞轮相关的新字段到现有表

    迁移内容：
    1. memory_logs 表添加 reward, outcome, evaluated_at 字段
    2. 创建 rl_training_samples 表
    3. 创建 rl_model_checkpoints 表
    """
    async with async_session() as session:
        try:
            await session.execute(text("""
                ALTER TABLE memory_logs
                ADD COLUMN IF NOT EXISTS reward DOUBLE PRECISION,
                ADD COLUMN IF NOT EXISTS outcome JSONB DEFAULT '{}',
                ADD COLUMN IF NOT EXISTS evaluated_at TIMESTAMP;
            """))

            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_log_reward ON memory_logs(reward);
            """))

            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_log_evaluated ON memory_logs(evaluated_at);
            """))

            await session.commit()
            print("成功为 memory_logs 表添加 RL 相关字段和索引")

        except Exception as e:
            await session.rollback()
            print(f"迁移失败: {e}")
            raise

        try:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS rl_training_samples (
                    id VARCHAR PRIMARY KEY,
                    log_id VARCHAR NOT NULL,
                    entity_id VARCHAR NOT NULL,
                    entity_type VARCHAR NOT NULL,
                    state JSONB NOT NULL,
                    action VARCHAR NOT NULL,
                    reward DOUBLE PRECISION NOT NULL,
                    next_state JSONB,
                    done BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))

            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_rl_log_id ON rl_training_samples(log_id);
            """))

            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_rl_entity ON rl_training_samples(entity_type, entity_id);
            """))

            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_rl_reward ON rl_training_samples(reward);
            """))

            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_rl_created_at ON rl_training_samples(created_at);
            """))

            await session.commit()
            print("成功创建 rl_training_samples 表和索引")

        except Exception as e:
            await session.rollback()
            print(f"创建 rl_training_samples 表失败: {e}")
            raise

        try:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS rl_model_checkpoints (
                    id VARCHAR PRIMARY KEY,
                    model_name VARCHAR NOT NULL,
                    version VARCHAR NOT NULL,
                    model_data JSONB NOT NULL,
                    metrics JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))

            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_rl_model_name ON rl_model_checkpoints(model_name);
            """))

            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_rl_model_version ON rl_model_checkpoints(version);
            """))

            await session.commit()
            print("成功创建 rl_model_checkpoints 表和索引")

        except Exception as e:
            await session.rollback()
            print(f"创建 rl_model_checkpoints 表失败: {e}")
            raise

    print("数据库迁移完成！")


async def rollback_rl_fields():
    """
    回滚 RL 飞轮相关的更改

    注意：这会删除 RL 相关的表和字段，请谨慎使用！
    """
    async with async_session() as session:
        try:
            await session.execute(text("""
                DROP INDEX IF EXISTS idx_log_reward;
                DROP INDEX IF EXISTS idx_log_evaluated;
            """))
            await session.commit()
            print("已删除索引")

        except Exception as e:
            await session.rollback()
            print(f"删除索引失败: {e}")

        try:
            await session.execute(text("""
                ALTER TABLE memory_logs
                DROP COLUMN IF EXISTS reward,
                DROP COLUMN IF EXISTS outcome,
                DROP COLUMN IF EXISTS evaluated_at;
            """))
            await session.commit()
            print("已从 memory_logs 表删除 RL 字段")

        except Exception as e:
            await session.rollback()
            print(f"删除字段失败: {e}")

        try:
            await session.execute(text("""
                DROP TABLE IF EXISTS rl_model_checkpoints;
            """))
            await session.commit()
            print("已删除 rl_model_checkpoints 表")

        except Exception as e:
            await session.rollback()
            print(f"删除 rl_model_checkpoints 表失败: {e}")

        try:
            await session.execute(text("""
                DROP TABLE IF EXISTS rl_training_samples;
            """))
            await session.commit()
            print("已删除 rl_training_samples 表")

        except Exception as e:
            await session.rollback()
            print(f"删除 rl_training_samples 表失败: {e}")

    print("回滚完成！")


async def check_migration_status():
    """检查迁移状态"""
    async with async_session() as session:
        status = {}

        result = await session.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'memory_logs'
            AND column_name IN ('reward', 'outcome', 'evaluated_at');
        """))
        status["memory_logs_columns"] = [(row[0], row[1]) for row in result.fetchall()]

        result = await session.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name IN ('rl_training_samples', 'rl_model_checkpoints');
        """))
        status["rl_tables"] = [row[0] for row in result.fetchall()]

        result = await session.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'memory_logs'
            AND indexname IN ('idx_log_reward', 'idx_log_evaluated');
        """))
        status["memory_logs_indexes"] = [row[0] for row in result.fetchall()]

        return status


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python migrate_rl.py migrate    # 执行迁移")
        print("  python migrate_rl.py rollback  # 回滚")
        print("  python migrate_rl.py status    # 检查状态")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "migrate":
        asyncio.run(migrate_add_rl_fields())
    elif command == "rollback":
        print("警告：这将删除所有 RL 相关的数据！")
        confirm = input("确定要继续吗？(yes/no): ")
        if confirm.lower() == "yes":
            asyncio.run(rollback_rl_fields())
        else:
            print("已取消")
    elif command == "status":
        status = asyncio.run(check_migration_status())
        print("迁移状态:")
        print(f"  memory_logs 表中的 RL 字段: {status['memory_logs_columns']}")
        print(f"  RL 表: {status['rl_tables']}")
        print(f"  memory_logs 表的 RL 索引: {status['memory_logs_indexes']}")
    else:
        print(f"未知命令: {command}")
        sys.exit(1)
