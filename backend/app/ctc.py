import logging
import os
import cv2
import math
from pathlib import Path
from typing import Tuple, List, Optional
import numpy as np
import scipy.signal as ss
from skimage import morphology, filters, segmentation


logger = logging.getLogger(__name__)


class CTCAnalyzer:
    """循环肿瘤细胞荧光图像分析器"""

    def __init__(self, file_path: str, file_save_path: str, roundness_threshold: float = 0.3):
        """
        初始化分析器

        Args:
            file_path: 输入文件路径
            file_save_path: 输出文件路径
            roundness_threshold: 圆度阈值
        """
        self.file_path = file_path
        self.file_save_path = file_save_path
        self.roundness_threshold = roundness_threshold

        # 子文件夹列表
        self.sub_file_path_list = ['1', '2', '3', '4', '5']

        # 结果存储
        self.results = {
            'green_single_channel': [],
            'white_single_channel': [],
            'ctc_areas': [],
            'wbc_areas': [],
            'blue_cells': [],
            'green_cells': [],
            'doc_names': [],
            'file_names': [],
            'all_areas': [],
            'roundness_values': [],
            'ctc_image_sets': []
        }

    def compute_roundness(self, label_image: np.ndarray) -> Tuple[List, List]:
        """
        计算轮廓的圆度

        Args:
            label_image: 二值标签图像

        Returns:
            contours: 轮廓列表
            roundness_list: 圆度列表
        """
        contours, _ = cv2.findContours(label_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        roundness_list = []

        for contour in contours:
            area = cv2.contourArea(contour) * 4 * math.pi
            perimeter_squared = math.pow(cv2.arcLength(contour, True), 2)

            roundness = area / perimeter_squared if perimeter_squared != 0 else 0
            roundness_list.append(roundness)

        return contours, roundness_list

    def watershed_segmentation(self, blue_channel: np.ndarray, original_image: np.ndarray,
                               mean_intensity: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        使用分水岭算法进行细胞分割

        Args:
            blue_channel: 蓝色通道图像
            original_image: 原始图像
            mean_intensity: 平均强度值

        Returns:
            dilated: 膨胀后的图像
            result_image: 结果图像
        """
        # 计算梯度
        gradient = filters.rank.gradient(blue_channel, morphology.disk(3))

        # 创建结构元素
        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        kernel_large = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        kernel1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1, 1))
        kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))

        # 阈值处理
        _, thresh1 = cv2.threshold(gradient, 12, 255, cv2.THRESH_TOZERO)
        _, thresh2 = cv2.threshold(thresh1, 254, 255, cv2.THRESH_TOZERO_INV)
        _, binary_thresh = cv2.threshold(thresh2, 10, 255, cv2.THRESH_BINARY)
        _, thresh3 = cv2.threshold(blue_channel, mean_intensity + 20, 255, cv2.THRESH_BINARY)

        # 形态学操作
        eroded1 = cv2.erode(binary_thresh, kernel_small)
        dilated1 = cv2.dilate(eroded1, kernel_large)
        eroded2 = cv2.erode(thresh3, kernel1)
        dilated2 = cv2.dilate(eroded2, kernel2)
        dilated = cv2.add(dilated1, dilated2)

        # 绘制轮廓
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        original_image[:, :, 2] = np.zeros_like(blue_channel)
        result_image = cv2.drawContours(original_image, contours, -1, (0, 0, 255), -1)

        return dilated, result_image

    def preprocess_image(self, image_path: str, median_filter_size: int = 3) -> np.ndarray:
        """
        预处理图像

        Args:
            image_path: 图像路径
            median_filter_size: 中值滤波器大小

        Returns:
            processed_image: 处理后的图像
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法读取图像: {image_path}")

        # 应用中值滤波
        for i in range(3):
            image[:, :, i] = ss.medfilt2d(image[:, :, i], [median_filter_size, median_filter_size])

        return image

    def enhance_channel(self, channel: np.ndarray, mean_intensity: float,
                        enhancement_factor: float = 3.0) -> np.ndarray:
        """
        增强通道对比度

        Args:
            channel: 输入通道
            mean_intensity: 平均强度
            enhancement_factor: 增强因子

        Returns:
            enhanced_channel: 增强后的通道
        """
        enhanced = (channel / mean_intensity * enhancement_factor).astype(np.uint8)
        enhanced = cv2.add(enhanced, enhanced)  # 双重增强
        enhanced1 = cv2.add(enhanced, enhanced)
        enhanced1 = cv2.add(enhanced1, enhanced1)

        # 应用中值滤波
        for i in range(3):
            enhanced[:, :, i] = ss.medfilt2d(enhanced[:, :, i], [7, 7])
            enhanced1[:, :, i] = ss.medfilt2d(enhanced1[:, :, i], [7, 7])
        return enhanced, enhanced1

    def analyze_cell_fluorescence(self, enhanced_green_channel: np.ndarray, enhanced_red_channel: np.ndarray,
                                  contour: np.ndarray, bounding_rect: Tuple) -> Tuple[bool, bool]:
        """
        分析细胞的荧光表达

        Args:
            enhanced_green_channel: 增强后的绿色通道
            enhanced_red_channel: 增强后的红色通道
            contour: 细胞轮廓
            bounding_rect: 边界矩形 (x, y, w, h)

        Returns:
            is_ctc: 是否为CTC细胞
            is_wbc: 是否为白细胞
        """
        x, y, w, h = bounding_rect

        # 检查细胞尺寸是否合理
        if (h > 70) or (w > 70) or (h / w > 2.5) or (w / h > 2.5) or (h < 2) or (w < 2):
            return False, False

        # 提取ROI区域
        green_roi = enhanced_green_channel[y:y + h, x:x + w]
        red_roi = enhanced_red_channel[y:y + h, x:x + w]

        # 计算荧光强度
        green_intensity = np.mean(green_roi[green_roi > 5]) if np.any(green_roi > 5) else 0
        red_intensity = np.mean(red_roi[red_roi > 5]) if np.any(red_roi > 5) else 0

        # 计算最大强度
        green_max = np.max(green_roi)
        red_max = np.max(red_roi)

        # 计算平均强度（排除边界）
        green_mean_inner = np.mean(green_roi[1:h - 1, 1:w - 1]) if h > 2 and w > 2 else green_intensity
        green_mean_outer = np.mean(green_roi)

        red_mean_inner = np.mean(red_roi[1:h - 1, 1:w - 1]) if h > 2 and w > 2 else red_intensity
        red_mean_outer = np.mean(red_roi)

        # CTC判断条件
        ctc_condition1 = (green_max > 15) and (red_max < 20)
        ctc_condition2 = (green_intensity > 15) and (red_intensity < 20)

        # WBC判断条件
        wbc_condition1 = (red_max > 20) and (green_max < 20)
        wbc_condition2 = (red_intensity > 20) and (green_intensity < 20)

        is_ctc = ctc_condition1 or ctc_condition2
        is_wbc = wbc_condition1 or wbc_condition2

        # 排除双重阳性和太小的细胞
        contour_area = contour.shape[0]
        equivalent_diameter = math.sqrt(4 * contour_area / math.pi) * 100 / 231

        if ((green_intensity > 90 and red_intensity > 90) or equivalent_diameter < 2):
            return False, False

        return is_ctc, is_wbc

    def process_single_image(self, blue_image_path: str, sub_folder: str) -> Tuple[int, int]:
        """
        处理单张蓝色通道图像及其对应的绿色和红色通道

        Args:
            blue_image_path: 蓝色图像路径
            sub_folder: 子文件夹名称

        Returns:
            ctc_count: CTC细胞计数
            wbc_count: 白细胞计数
        """
        # 解析文件名
        file_name = os.path.basename(blue_image_path)
        base_name = file_name.split('.')[0]  # 去除扩展名
        color_suffix = base_name[-1]  # 现在获取的是基名的最后一个字符

        # 确定对应的绿色和红色图像文件名
        if color_suffix == 'b':
            green_file = base_name[:-1] + 'g.' + file_name.split('.')[-1]
            red_file = base_name[:-1] + 'r.' + file_name.split('.')[-1]
        else:
            green_file = base_name[:-1] + 'G.' + file_name.split('.')[-1]
            red_file = base_name[:-1] + 'R.' + file_name.split('.')[-1]

        # 构建完整路径
        folder_path = os.path.dirname(blue_image_path)
        green_image_path = os.path.join(folder_path, green_file)
        red_image_path = os.path.join(folder_path, red_file)

        # 检查对应的绿色和红色图像是否存在
        if not os.path.exists(green_image_path):
            logger.warning("警告: 找不到绿色图像 %s", green_image_path)
            return 0, 0
        if not os.path.exists(red_image_path):
            logger.warning("警告: 找不到红色图像 %s", red_image_path)
            return 0, 0

        # 预处理图像
        blue_img = self.preprocess_image(blue_image_path)
        green_img = self.preprocess_image(green_image_path)
        red_img = self.preprocess_image(red_image_path)

        # 提取通道
        blue_channel, _, _ = cv2.split(blue_img)
        _, green_channel, _ = cv2.split(green_img)
        _, _, red_channel = cv2.split(red_img)

        # 增强所有通道
        mean_blue = np.mean(blue_channel)
        mean_blue1 = np.mean(blue_channel[blue_channel[:, :] > 15])
        mean_green = np.mean(green_channel)
        mean_red = np.mean(red_channel)

        # 增强蓝色通道
        enhanced_blue, enhanced_blue1 = self.enhance_channel(blue_img, mean_blue)
        enhanced_blue_channel, _, _ = cv2.split(enhanced_blue)

        # 增强绿色通道
        enhanced_green, _ = self.enhance_channel(green_img, mean_green)
        _, enhanced_green_channel, _ = cv2.split(enhanced_green)

        # 增强红色通道
        enhanced_red, _ = self.enhance_channel(red_img, mean_red)
        _, _, enhanced_red_channel = cv2.split(enhanced_red)

        # 应用分水岭分割
        segmented_mask, result_img = self.watershed_segmentation(
            enhanced_blue_channel, blue_img.copy(), mean_blue1
        )

        # 分析细胞
        contours, roundness_values = self.compute_roundness(segmented_mask)

        ctc_count = 0
        wbc_count = 0

        # 创建用于绘制矩形框的增强图像副本
        enhanced_blue_with_boxes = enhanced_blue.copy()
        enhanced_green_with_boxes = enhanced_green.copy()
        enhanced_red_with_boxes = enhanced_red.copy()

        ctc_only_blue = enhanced_blue.copy()
        ctc_only_green = enhanced_green.copy()
        ctc_only_red = enhanced_red.copy()
        found_ctc = False

        for i, (contour, roundness) in enumerate(zip(contours, roundness_values)):
            area = cv2.contourArea(contour)
            bounding_rect = cv2.boundingRect(contour)

            # 应用圆度和面积筛选
            if (roundness > self.roundness_threshold and
                    30 < area < 3000 and
                    self._validate_blue_intensity(enhanced_blue, bounding_rect)):

                # 在增强后的通道上分析荧光
                is_ctc, is_wbc = self.analyze_cell_fluorescence(
                    enhanced_green_channel, enhanced_red_channel, contour, bounding_rect
                )

                if is_ctc:
                    ctc_count += 1
                    found_ctc = True
                    # 在增强后的图像上标记细胞
                    self._mark_cell(enhanced_blue_with_boxes, enhanced_green_with_boxes,
                                    enhanced_red_with_boxes, bounding_rect, 'ctc')
                    self._draw_rectangle(
                        [ctc_only_blue, ctc_only_green, ctc_only_red],
                        bounding_rect,
                        (255, 255, 255)
                    )

                elif is_wbc:
                    wbc_count += 1
                    # 在增强后的图像上标记细胞
                    self._mark_cell(enhanced_blue_with_boxes, enhanced_green_with_boxes,
                                    enhanced_red_with_boxes, bounding_rect, 'wbc')

        # 保存增强后的结果图像（带框选）
        blue_save_path, green_save_path, red_save_path, _ = self._save_results(
            enhanced_blue_with_boxes,
            enhanced_green_with_boxes,
            enhanced_red_with_boxes,
            segmented_mask,
            sub_folder,
            file_name,
            green_file,
            red_file
        )

        if found_ctc:
            ctc_blue_path, ctc_green_path, ctc_red_path = self._save_ctc_highlights(
                ctc_only_blue,
                ctc_only_green,
                ctc_only_red,
                sub_folder,
                file_name,
                green_file,
                red_file
            )
            self.results['ctc_image_sets'].append({
                'sub_folder': sub_folder,
                'blue_path': ctc_blue_path,
                'green_path': ctc_green_path,
                'red_path': ctc_red_path,
                'blue_original': blue_save_path,
                'green_original': green_save_path,
                'red_original': red_save_path
            })

        return ctc_count, wbc_count

    def _validate_blue_intensity(self, blue_image: np.ndarray,
                                 bounding_rect: Tuple) -> bool:
        """
        验证蓝色通道强度

        Args:
            blue_image: 蓝色图像
            bounding_rect: 边界矩形

        Returns:
            is_valid: 强度是否有效
        """
        x, y, w, h = bounding_rect

        # 计算中心区域强度
        center_region = blue_image[
                        y + round(0.25 * h):y + h - round(0.25 * h),
                        x + round(0.25 * w):x + w - round(0.25 * w), 0
                        ]

        # 计算整体区域强度
        whole_region = blue_image[y:y + h, x:x + w, 0]

        return np.mean(center_region) > np.mean(whole_region)

    def _mark_cell(self, blue_img: np.ndarray, green_img: np.ndarray,
                   red_img: np.ndarray, bounding_rect: Tuple, cell_type: str):
        """
        标记检测到的细胞

        Args:
            blue_img: 蓝色图像
            green_img: 绿色图像
            red_img: 红色图像
            bounding_rect: 边界矩形
            cell_type: 细胞类型 ('ctc' 或 'wbc')
        """
        x, y, w, h = bounding_rect

        if cell_type == 'ctc':
            color = (255, 255, 255)  # 白色框
        else:  # wbc
            color = (255, 0, 0)  # 蓝色框

        # 在三个通道上绘制矩形
        for img in [blue_img, green_img, red_img]:
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 1)

    def _draw_rectangle(self, images: List[np.ndarray], bounding_rect: Tuple,
                        color: Tuple[int, int, int]) -> None:
        """在给定图像列表上绘制矩形框"""
        x, y, w, h = bounding_rect
        for img in images:
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 1)

    def _save_results(self, blue_img: np.ndarray, green_img: np.ndarray,
                      red_img: np.ndarray, segmented_mask: np.ndarray,
                      sub_folder: str, blue_name: str, green_name: str,
                      red_name: str) -> Tuple[str, str, str, str]:
        """
        保存结果图像（包含分割掩码）并返回保存路径

        Args:
            blue_img: 蓝色图像（增强后带框选）
            green_img: 绿色图像（增强后带框选）
            red_img: 红色图像（增强后带框选）
            segmented_mask: 分割掩码
            sub_folder: 子文件夹
            blue_name: 蓝色通道文件名
            green_name: 绿色通道文件名
            red_name: 红色通道文件名

        Returns:
            包含蓝色、绿色、红色通道图像及掩码的保存路径
        """
        save_folder = Path(self.file_save_path) / sub_folder
        save_folder.mkdir(parents=True, exist_ok=True)

        blue_path = save_folder / blue_name
        green_path = save_folder / green_name
        red_path = save_folder / red_name

        blue_stem = blue_path.stem
        mask_name = f"{blue_stem}_mask{blue_path.suffix}"
        mask_path = save_folder / mask_name

        cv2.imwrite(str(blue_path), blue_img)
        cv2.imwrite(str(green_path), green_img)
        cv2.imwrite(str(red_path), red_img)
        cv2.imwrite(str(mask_path), segmented_mask)

        return str(blue_path), str(green_path), str(red_path), str(mask_path)

    def _save_ctc_highlights(self, blue_img: np.ndarray, green_img: np.ndarray,
                             red_img: np.ndarray, sub_folder: str,
                             blue_name: str, green_name: str,
                             red_name: str) -> Tuple[str, str, str]:
        """
        保存仅标注CTC的结果图像，并返回保存路径

        Args:
            blue_img: 蓝色通道图像（仅含CTC标记）
            green_img: 绿色通道图像（仅含CTC标记）
            red_img: 红色通道图像（仅含CTC标记）
            sub_folder: 子文件夹
            blue_name: 蓝色通道原始文件名
            green_name: 绿色通道原始文件名
            red_name: 红色通道原始文件名

        Returns:
            蓝色、绿色、红色通道CTC高亮图像的保存路径
        """
        highlight_folder = Path(self.file_save_path) / sub_folder / "ctc"
        highlight_folder.mkdir(parents=True, exist_ok=True)

        blue_path = highlight_folder / f"{Path(blue_name).stem}_ctc{Path(blue_name).suffix}"
        green_path = highlight_folder / f"{Path(green_name).stem}_ctc{Path(green_name).suffix}"
        red_path = highlight_folder / f"{Path(red_name).stem}_ctc{Path(red_name).suffix}"

        cv2.imwrite(str(blue_path), blue_img)
        cv2.imwrite(str(green_path), green_img)
        cv2.imwrite(str(red_path), red_img)

        return str(blue_path), str(green_path), str(red_path)

    def process_all_images(self):
        """处理所有图像"""
        txt_save_name = f"{self.file_path}.txt"

        # 处理每个子文件夹
        for sub_folder in self.sub_file_path_list:
            folder_path = os.path.join(self.file_path, sub_folder)

            if not os.path.exists(folder_path):
                logger.warning("警告: 文件夹 %s 不存在，跳过", folder_path)
                continue

            ctc_total = 0
            wbc_total = 0

            # 处理文件夹中的每个文件
            for file_name in os.listdir(folder_path):
                if file_name == '.DS_Store':
                    continue

                file_path_full = os.path.join(folder_path, file_name)

                # 修正：先获取文件名的基名（不含扩展名），再检查最后一个字符
                base_name = os.path.splitext(file_name)[0]  # 去除扩展名
                if len(base_name) > 0 and base_name[-1].lower() == 'b':
                    try:
                        logger.info("处理蓝色图像: %s", file_name)
                        ctc_count, wbc_count = self.process_single_image(file_path_full, sub_folder)
                        ctc_total += ctc_count
                        wbc_total += wbc_count
                        logger.info("  - CTC: %s, WBC: %s", ctc_count, wbc_count)

                    except Exception as e:
                        logger.exception("处理图像 %s 时出错", file_path_full)
                        continue
                else:
                    logger.debug("跳过非蓝色图像: %s", file_name)

            # 保存该文件夹的结果
            self.results['green_single_channel'].append(ctc_total)
            self.results['white_single_channel'].append(wbc_total)
            self.results['doc_names'].append(sub_folder)

            logger.info("通道 %s 统计: CTC总数=%s, WBC总数=%s", sub_folder, ctc_total, wbc_total)

        # 保存结果到文件
        self._save_results_to_file(txt_save_name)

    def _save_results_to_file(self, file_path: str):
        """
        保存结果到文本文件

        Args:
            file_path: 文件路径
        """
        with open(file_path, 'w') as f:
            f.write(f'green_single_channel {self.results["green_single_channel"]}\n')
            f.write(f'white_single_channel {self.results["white_single_channel"]}\n')



def main():
    """主函数"""
    file_path = 'a'
    file_save_path = 'b'

    analyzer = CTCAnalyzer(file_path, file_save_path)
    analyzer.process_all_images()
    logger.info("处理完成！")


if __name__ == "__main__":
    main()