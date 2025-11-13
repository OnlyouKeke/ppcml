<template>
  <div class="report-builder">
    <header class="page-header">
      <div class="page-heading">
        <h2 class="page-title">报告生成工作台</h2>
        <p class="page-subtitle">整合宠物信息与识别结果，一键生成专业报告文本</p>
      </div>
    </header>

    <section class="layout">
      <el-card shadow="hover" class="form-card">
        <template #header>
          <div class="card-title">基础信息填写</div>
        </template>
        <el-form :model="form" label-width="120px" label-position="left" class="info-form">
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="宠主姓名">
                  <el-input v-model="form.ownerName" placeholder="宠主姓名" clearable />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="宠物姓名">
                  <el-input v-model="form.petName" placeholder="宠物姓名" clearable />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="性别">
                  <el-select v-model="form.gender" placeholder="请选择性别" clearable>
                    <el-option label="公" value="公" />
                    <el-option label="母" value="母" />
                    <el-option label="未知" value="未知" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="宠物类型">
                  <el-radio-group v-model="form.petType">
                    <el-radio label="猫">猫</el-radio>
                    <el-radio label="狗">狗</el-radio>
                    <el-radio label="其他">其他</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="年龄">
                  <el-input v-model="form.age" placeholder="2岁3个月" clearable />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="送检单位">
                  <el-input v-model="form.institutionName" placeholder="请输入机构名称" clearable />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="送检时间">
                  <el-date-picker
                    v-model="form.detectionDate"
                    type="date"
                    placeholder="请选择检测日期"
                    value-format="YYYY-MM-DD"
                    style="width: 100%"
                    clearable
                  />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="科别">
                  <el-input v-model="form.department" placeholder="请输入科别" clearable />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="癌症标志物">
                  <el-input v-model="form.cancerBiomarker" placeholder="请输入癌症标志物" clearable />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="样本类型">
                  <el-input v-model="form.sampleType" placeholder="请输入标本类型" clearable />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="样品量（单位ml）">
                  <el-input
                    v-model="form.sampleVolume"
                    placeholder="请输入样品量"
                    type="number"
                    clearable
                  />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="样本编号">
                  <el-input
                    v-model="form.sampleNumber"
                    :maxlength="sampleNumberMaxLength"
                    :disabled="!form.petType"
                    placeholder="请选择宠物类型后填写"
                    @input="handleSampleNumberInput"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16" class="form-row">
              <el-col :xs="24" :sm="12">
                <el-form-item label="样本状态">
                  <el-radio-group v-model="form.sampleStatus">
                    <el-radio label="合格">合格</el-radio>
                    <el-radio label="不合格">不合格</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="一周内是否有药物摄入">
                  <el-radio-group v-model="form.medicationIntake">
                    <el-radio label="是">是</el-radio>
                    <el-radio label="否">否</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="如有，请说明">
              <el-input
                v-model="form.notes"
                type="textarea"
                :rows="3"
                placeholder="既往病史、当前症状等"
                resize="none"
              />
            </el-form-item>
            <el-form-item label="影像导入">
              <div class="upload-area">
                <input
                  ref="fileInputRef"
                  class="upload-input"
                  type="file"
                  webkitdirectory
                  multiple
                  @change="handleFolderChange"
                />
                <el-button
                  type="primary"
                  plain
                  :disabled="!selectedFiles.length"
                  :loading="isDetecting"
                  @click="runDetection"
                >
                  {{ isDetecting ? '生成中...' : '生成报告' }}
                </el-button>
                <div v-if="selectedFiles.length" class="file-name">
                  {{ selectedFolderName || '已选文件夹' }}（{{ folderFileCount }} 个文件）
                </div>
                <div v-else class="upload-tip">请选择包含五个通道的影像文件夹</div>
                <div class="output-folder-section">
                  <div class="output-folder-selector">
                    <el-input
                      v-model="form.outputDirPath"
                      placeholder="请输入或选择输出文件夹路径"
                      clearable
                      class="output-folder-input"
                    >
                      <template #append>
                        <el-button
                          type="primary"
                          plain
                          @click="triggerOutputFolderSelection"
                        >
                          选择输出文件夹
                        </el-button>
                      </template>
                    </el-input>
                  </div>
                  <div class="output-folder-tip">
                    若路径不存在将自动创建，并在其中输出处理结果与 Word 报告。
                  </div>
                </div>
              </div>
            </el-form-item>
        </el-form>
      </el-card>
      
      <el-card shadow="hover" class="mask-card">
        <template #header>
          <div class="card-title">掩码图像选择</div>
        </template>
        <div class="mask-selection">
          <p class="mask-instruction">请选择需要插入 Word 报告的三个通道掩码图像。</p>
          <div v-if="maskDirectoryPath" class="mask-directory">
            掩码图像来源文件夹：<span class="mask-directory-path">{{ maskDirectoryPath }}</span>
          </div>
          <div v-if="isPreviewLoading" class="mask-loading">
            <el-skeleton :rows="3" animated />
          </div>
          <div v-else-if="!reportToken" class="mask-placeholder">
            生成报告预览后，将在此展示生成的所有图像供选择。
          </div>
          <el-empty
            v-else-if="!maskOptions.length"
            description="当前未检测到可用的掩码图像"
            :image-size="100"
            class="mask-empty"
          />
          <div v-else class="mask-options-wrapper">
            <div class="mask-preview-grid">
              <div
                v-for="option in maskOptions"
                :key="`preview-${option.id}`"
                :class="[
                  'mask-preview-item',
                  { active: maskSelectionOrderMap.get(option.id) }
                ]"
                @click="toggleMaskSelection(option.id)"
              >
                <img
                  :src="`data:${option.mimeType};base64,${option.data}`"
                  :alt="option.label"
                  class="mask-preview-image"
                />
                <div class="mask-preview-label">
                  {{ option.label }}
                  <el-tag
                    v-if="maskSelectionOrderMap.get(option.id)"
                    size="small"
                    class="mask-selection-order"
                  >
                    第{{ maskSelectionOrderMap.get(option.id) }}张
                  </el-tag>
                </div>
              </div>
            </div>
            <div class="mask-selected-tip">
              已选择 {{ selectedMaskOptions.length }} / {{ requiredMaskSelectionCount }} 张掩码图像
            </div>
            <div v-if="!isMaskSelectionComplete" class="mask-selection-warning">
              请从上述掩码图像中选择 {{ requiredMaskSelectionCount }} 张，将用于报告预览与导出。
            </div>
          </div>
        </div>
      </el-card>

      <el-card shadow="hover" class="preview-card">
        <template #header>
          <div class="card-title">报告预览</div>
        </template>
        <div class="preview-wrapper">
            <div v-if="isPreviewLoading" class="preview-loading">
              <el-skeleton :rows="8" animated />
            </div>
            <div
              v-else-if="reportData && isMaskSelectionComplete"
              class="preview-content"
            >
              <div class="report-preview">
                <header class="report-header">
                  <div class="report-title">
                    <div class="report-title-line">
                      <span class="report-title-brand">FlowCanis</span>
                      <span class="report-title-text">微流控循环肿瘤细胞分选</span>
                    </div>
                    <div class="report-title-line report-title-line--secondary">
                      与免疫荧光识别检测报告单
                    </div>
                  </div>
                  <div class="report-divider">
                    <span class="report-divider-line report-divider-line--primary" />
                    <span class="report-divider-line report-divider-line--secondary" />
                  </div>
                  <div class="report-number">编号：{{ reportNumberDisplay }}</div>
                </header>
                <div class="report-generated-at">
                  生成时间：{{ formatGeneratedAt(reportData.generatedAt) }}
                </div>
                <section class="report-info">
                  <div
                    v-for="(row, rowIndex) in previewInfoRows"
                    :key="rowIndex"
                    class="report-info-row"
                  >
                    <div
                      v-for="(field, fieldIndex) in row"
                      :key="fieldIndex"
                      class="report-info-cell"
                      :class="{
                        'report-info-cell--wide': field.span === 2,
                        'report-info-cell--full': field.span === 4
                      }"
                    >
                      <span class="report-info-label">{{ field.label }}：</span>
                      <span class="report-info-value">{{ field.value }}</span>
                    </div>
                  </div>
                </section>
                <section v-if="channelPreviewItems.length" class="report-section">
                  <h4 class="section-title">通道图像</h4>
                  <div v-if="channelSummaryTexts.length" class="channel-summary-texts">
                    <p
                      v-for="(text, index) in channelSummaryTexts"
                      :key="`summary-${index}`"
                      class="channel-summary-text"
                    >
                      {{ text }}
                    </p>
                  </div>
                  <div class="channel-preview-grid">
                    <div
                      v-for="item in channelPreviewItems"
                      :key="item.label"
                      class="channel-preview-card"
                    >
                      <div class="channel-preview-label">{{ item.label }}</div>
                      <img
                        :src="item.src"
                        class="channel-preview-image"
                        :alt="`${item.label}预览图`"
                      />
                    </div>
                  </div>
                </section>
                <footer class="preview-footer">
                  检测人：______________&nbsp;&nbsp;&nbsp;&nbsp;审核人：______________&nbsp;&nbsp;&nbsp;&nbsp;报告日期：______________
                </footer>
                <div class="preview-disclaimer">
                  <p
                    v-for="(line, index) in disclaimerLines"
                    :key="index"
                    class="preview-disclaimer-line"
                  >
                    {{ line }}
                  </p>
                </div>
              </div>
            </div>
            <div
              v-else-if="reportData && !isMaskSelectionComplete"
              class="preview-blocker"
            >
              <el-empty
                description="请选择三张掩码图像后查看报告预览"
                :image-size="120"
              />
            </div>
            <el-empty v-else description="请先生成报告以查看预览" :image-size="120" />
          </div>
          <div v-if="previewError" class="preview-error">
            <el-alert type="error" :closable="false" show-icon>{{ previewError }}</el-alert>
          </div>
          <div v-if="previewWarnings.length" class="preview-warnings">
            <el-alert
              v-for="(message, index) in previewWarnings"
              :key="index"
              type="warning"
              :closable="false"
              show-icon
            >
              {{ message }}
            </el-alert>
          </div>
          <div class="preview-actions">
            <el-button
              type="success"
              :disabled="!canDownloadReport || isExporting"
              :loading="isExporting"
              @click="downloadDocx"
            >
              {{ isExporting ? '生成中...' : '导出 Word 报告' }}
            </el-button>
            <el-button :disabled="!hasReport" @click="resetAll">重置内容</el-button>
          </div>
        </el-card>
      </section>
    </div>
  </template>
