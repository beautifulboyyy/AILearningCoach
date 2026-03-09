<template>
  <div class="tasks-container">
    <div class="page-header">
      <h2>任务管理</h2>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
        新建任务
      </el-button>
    </div>

    <div class="filters">
      <el-radio-group v-model="filterStatus" @change="fetchTasks">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button label="todo">待开始</el-radio-button>
        <el-radio-button label="in_progress">进行中</el-radio-button>
        <el-radio-button label="completed">已完成</el-radio-button>
      </el-radio-group>
      <el-input
        v-model="searchKeyword"
        placeholder="搜索任务..."
        :prefix-icon="Search"
        style="width: 300px"
        clearable
      />
    </div>

    <el-row :gutter="24" class="board-row" v-loading="loading">
      <el-col :xs="24" :lg="8">
        <el-card class="task-column">
          <template #header>
            <span class="column-title">待开始 ({{ pendingTasks.length }})</span>
          </template>
          <div class="task-list">
            <TaskCard
              v-for="task in filteredPendingTasks"
              :key="task.id"
              :task="task"
              @edit="handleEdit"
              @delete="handleDelete"
              @complete="handleComplete"
            />
            <el-empty v-if="filteredPendingTasks.length === 0" description="暂无任务" />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card class="task-column">
          <template #header>
            <span class="column-title">进行中 ({{ inProgressTasks.length }})</span>
          </template>
          <div class="task-list">
            <TaskCard
              v-for="task in filteredInProgressTasks"
              :key="task.id"
              :task="task"
              @edit="handleEdit"
              @delete="handleDelete"
              @complete="handleComplete"
            />
            <el-empty v-if="filteredInProgressTasks.length === 0" description="暂无任务" />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card class="task-column">
          <template #header>
            <span class="column-title">已完成 ({{ completedTasks.length }})</span>
          </template>
          <div class="task-list">
            <TaskCard
              v-for="task in filteredCompletedTasks"
              :key="task.id"
              :task="task"
              @edit="handleEdit"
              @delete="handleDelete"
            />
            <el-empty v-if="filteredCompletedTasks.length === 0" description="暂无任务" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 创建任务对话框 -->
    <TaskDialog
      v-model="showCreateDialog"
      @confirm="handleCreate"
    />
    
    <!-- 编辑任务对话框 -->
    <TaskDialog
      v-model="showEditDialog"
      :task="editingTask"
      @confirm="handleUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { useTaskStore } from '@/stores/task'
import TaskCard from '@/components/task/TaskCard.vue'
import TaskDialog from '@/components/task/TaskDialog.vue'

const taskStore = useTaskStore()

const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const editingTask = ref<any>(null)
const filterStatus = ref('')
const searchKeyword = ref('')

const loading = computed(() => taskStore.loading)
const pendingTasks = computed(() => taskStore.pendingTasks)
const inProgressTasks = computed(() => taskStore.inProgressTasks)
const completedTasks = computed(() => taskStore.completedTasks)

const filteredPendingTasks = computed(() => filterTasks(pendingTasks.value))
const filteredInProgressTasks = computed(() => filterTasks(inProgressTasks.value))
const filteredCompletedTasks = computed(() => filterTasks(completedTasks.value))

const filterTasks = (tasks: any[]) => {
  let result = tasks
  if (searchKeyword.value) {
    result = result.filter(t => 
      t.title.toLowerCase().includes(searchKeyword.value.toLowerCase())
    )
  }
  return result
}

const fetchTasks = async () => {
  await taskStore.fetchTasks()
}

const handleCreate = async (data: any) => {
  try {
    await taskStore.createTask(data)
    ElMessage.success('任务创建成功')
    showCreateDialog.value = false
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

const handleEdit = async (task: any) => {
  editingTask.value = task
  showEditDialog.value = true
}

const handleUpdate = async (data: any) => {
  try {
    await taskStore.updateTask(editingTask.value.id, data)
    ElMessage.success('任务更新成功')
    showEditDialog.value = false
    editingTask.value = null
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

const handleDelete = async (id: string | number) => {
  await ElMessageBox.confirm('确定删除此任务？', '提示', {
    type: 'warning'
  })
  try {
    await taskStore.deleteTask(id)
    ElMessage.success('删除成功')
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const handleComplete = async (id: string | number) => {
  try {
    await taskStore.completeTask(id)
    ElMessage.success('任务已完成')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

onMounted(() => {
  fetchTasks()
})
</script>

<style scoped lang="scss">
.tasks-container {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    
    h2 {
      margin: 0;
    }
  }
  
  .filters {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
  }
  
  .board-row {
    min-height: 500px;
  }
  
  .task-column {
    .column-title {
      font-weight: 500;
    }
    
    .task-list {
      min-height: 400px;
      max-height: 600px;
      overflow-y: auto;
    }
  }
}
</style>
