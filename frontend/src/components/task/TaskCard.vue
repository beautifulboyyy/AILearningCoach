<template>
  <div class="task-card">
    <div class="task-header">
      <span class="task-title">{{ task.title }}</span>
      <el-dropdown trigger="click" @command="handleCommand" @click.stop>
        <el-icon class="more-icon"><MoreFilled /></el-icon>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="edit">编辑</el-dropdown-item>
            <el-dropdown-item command="complete" v-if="task.status !== 'completed'">
              完成
            </el-dropdown-item>
            <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
    <p class="task-description">{{ task.description || '无描述' }}</p>
    <div class="task-footer">
      <el-tag :type="getPriorityType(task.priority)" size="small">
        {{ getPriorityLabel(task.priority) }}
      </el-tag>
      <span v-if="task.due_date" class="due-date">
        {{ formatDate(task.due_date) }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { MoreFilled } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/format'
import { PRIORITY_OPTIONS } from '@/utils/constants'

const props = defineProps<{ task: any }>()
const emit = defineEmits(['edit', 'delete', 'complete'])

const getPriorityType = (priority: string) => {
  const map: Record<string, any> = {
    low: 'success',
    medium: 'warning',
    high: 'danger',
    urgent: 'danger'
  }
  return map[priority] || 'info'
}

const getPriorityLabel = (priority: string) => {
  return PRIORITY_OPTIONS.find(o => o.value === priority)?.label || priority
}

const handleCommand = (command: string) => {
  // 根据命令类型发出正确的事件，传递task.id而不是整个task对象
  if (command === 'edit') {
    emit('edit', props.task)
  } else if (command === 'delete') {
    emit('delete', props.task.id)
  } else if (command === 'complete') {
    emit('complete', props.task.id)
  }
}
</script>

<style scoped lang="scss">
.task-card {
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #EBEEF5;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s;
  
  &:hover {
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  }
  
  .task-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
    
    .task-title {
      flex: 1;
      font-weight: 500;
      color: #303133;
    }
    
    .more-icon {
      cursor: pointer;
      color: #909399;
      
      &:hover {
        color: #409EFF;
      }
    }
  }
  
  .task-description {
    font-size: 14px;
    color: #606266;
    margin: 8px 0;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
  
  .task-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .due-date {
      font-size: 12px;
      color: #909399;
    }
  }
}
</style>
