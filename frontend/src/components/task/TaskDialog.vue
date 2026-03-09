<template>
  <el-dialog
    :model-value="modelValue"
    :title="isEdit ? '编辑任务' : '新建任务'"
    width="600px"
    @close="handleClose"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="任务标题" prop="title">
        <el-input v-model="form.title" placeholder="请输入任务标题" />
      </el-form-item>
      <el-form-item label="任务描述">
        <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入任务描述" />
      </el-form-item>
      <el-form-item label="优先级" prop="priority">
        <el-select v-model="form.priority" style="width: 100%">
          <el-option label="低" value="low" />
          <el-option label="中" value="medium" />
          <el-option label="高" value="high" />
          <el-option label="紧急" value="urgent" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态" prop="status" v-if="isEdit">
        <el-select v-model="form.status" style="width: 100%">
          <el-option label="待开始" value="todo" />
          <el-option label="进行中" value="in_progress" />
          <el-option label="已完成" value="completed" />
        </el-select>
      </el-form-item>
      <el-form-item label="截止日期">
        <el-date-picker v-model="form.due_date" type="date" style="width: 100%" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleConfirm">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import type { FormInstance } from 'element-plus'

const props = defineProps<{ 
  modelValue: boolean
  task?: any
}>()

const emit = defineEmits(['update:modelValue', 'confirm'])

const formRef = ref<FormInstance>()
const form = reactive({
  title: '',
  description: '',
  priority: 'medium',
  status: 'todo',
  due_date: null as any
})

const isEdit = computed(() => !!props.task)

const rules = {
  title: [{ required: true, message: '请输入任务标题', trigger: 'blur' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }]
}

// 监听 task 变化，填充表单
watch(() => props.task, (newTask) => {
  if (newTask) {
    form.title = newTask.title || ''
    form.description = newTask.description || ''
    form.priority = newTask.priority || 'medium'
    form.status = newTask.status || 'todo'
    form.due_date = newTask.due_date ? new Date(newTask.due_date) : null
  }
}, { immediate: true })

const handleClose = () => {
  emit('update:modelValue', false)
  // 延迟重置表单，避免关闭动画时看到表单清空
  setTimeout(() => {
    if (!isEdit.value) {
      resetForm()
    }
  }, 300)
}

const resetForm = () => {
  Object.assign(form, { 
    title: '', 
    description: '', 
    priority: 'medium',
    status: 'todo',
    due_date: null 
  })
  formRef.value?.clearValidate()
}

const handleConfirm = async () => {
  try {
    await formRef.value?.validate()
    emit('confirm', { ...form })
    if (!isEdit.value) {
      resetForm()
    }
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}
</script>
