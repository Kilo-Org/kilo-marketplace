# SEO Delivery Guard

**Skill quản trị phát triển và phát hành SEO cho tác nhân lập trình AI, phù hợp với các giới hạn chính thức của Google Search.**

[![Codex Skill](https://img.shields.io/badge/Codex-Skill-111827?logo=openai&logoColor=white)](../SKILL.md)
[![Version 0.1.0](https://img.shields.io/badge/version-0.1.0-2563eb)](../CHANGELOG.md)
[![MIT License](https://img.shields.io/badge/license-MIT-16a34a)](../LICENSE)
[![Documentation languages: 10](https://img.shields.io/badge/docs-10%20languages-7c3aed)](../README.md#documentation)
[![GitHub source](https://img.shields.io/badge/GitHub-pangxin12345%2Fseo--delivery--guard-181717?logo=github&logoColor=white)](https://github.com/pangxin12345/seo-delivery-guard)
[![Official website](https://img.shields.io/badge/website-once--email.com-0f766e?logo=googlechrome&logoColor=white)](https://once-email.com)
[![skills.sh](https://skills.sh/b/pangxin12345/seo-delivery-guard)](https://skills.sh/pangxin12345/seo-delivery-guard)

[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português do Brasil](README.pt-BR.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Tiếng Việt](README.vi.md)

Kiểm toán SEO phát hiện vấn đề. **SEO Delivery Guard giúp tác nhân lập trình AI đưa các phát hiện đã được chấp nhận qua triển khai, rà soát, phát hành và xác minh trên môi trường sản xuất.**

Skill này không thay thế trình thu thập dữ liệu, công cụ hiệu năng, phân tích nội dung, trình kiểm tra dữ liệu có cấu trúc, nghiên cứu SERP hay dữ liệu Search Console. Nó điều phối các khả năng sẵn có, áp dụng quy tắc của dự án và tách lỗi chặn phát hành khỏi đề xuất tùy chọn.

## Vì sao cần Skill này

- Canonical đúng trong mã nguồn có thể sai trong trang đã tạo.
- Bản dịch chưa được biên tập chuyên nghiệp có thể vào Sitemap quá sớm.
- Dữ liệu có cấu trúc có thể mô tả thông tin người dùng không nhìn thấy.
- Chỉ thị robots có thể bị nhầm với cơ chế kiểm soát truy cập.
- Điểm tổng hợp có thể che khuất lỗi chặn về lập chỉ mục hoặc quyền riêng tư.
- Bản ứng viên có thể đạt nhưng môi trường sản xuất trả về metadata khác.
- Một bản phát hành có thể được tuyên bố thành công trước khi công cụ tìm kiếm thu thập lại.

## Khả năng chính

- Chọn tổ hợp phân tích SEO tối thiểu phù hợp với từng thay đổi.
- Đọc quy tắc dự án về phát triển, quyền riêng tư, bản địa hóa, phân tích, quảng cáo, kiểm thử và phát hành.
- Giải quyết các khuyến nghị xung đột theo thứ tự thẩm quyền rõ ràng.
- Ghi lại nguồn, thời điểm, độ tin cậy, mức độ, hành động, lớp xác minh và ảnh hưởng hoàn tác.
- Giữ lỗi chặn cứng ở dạng nhị phân, không làm nhẹ bằng điểm trung bình.
- So sánh hợp đồng hiển thị với công cụ tìm kiếm trước và sau thay đổi.
- Tách biệt mã nguồn, sản phẩm tạo ra, trình duyệt, HTTP công khai, phòng thí nghiệm, dữ liệu bên thứ nhất và ước tính bên thứ ba.
- Giữ lập chỉ mục, thứ hạng, lưu lượng, rich results, duyệt quảng cáo và khả năng hiển thị AI ở trạng thái chờ cho đến khi được xác minh.
- Yêu cầu quyết định rõ ràng giữa giữ nguyên, cải thiện, hợp nhất, đặt `noindex` hoặc xóa; chỉ dùng 301 khi có đích thực sự tương đương, nếu không giữ trạng thái `404/410` trung thực.

## Những điều không thực hiện

- Không phải một crawler hay công cụ kiểm toán SEO tất cả trong một khác.
- Không yêu cầu nhà cung cấp, API, MCP hoặc Skill bổ trợ cụ thể.
- Không gửi URL, thay đổi thuộc tính, phát hành mã hoặc triển khai khi chưa có quyền trong nhiệm vụ.
- Không bảo đảm lập chỉ mục, thứ hạng, lưu lượng, rich results, duyệt quảng cáo hay trích dẫn AI.

## Đầu vào, đầu ra và giới hạn từ chối

Chỉ cung cấp URL công khai, đường dẫn kho mã, thay đổi dự kiến, đối tượng, ý định lập chỉ mục, ngôn ngữ và bằng chứng đã làm sạch cần thiết. Không cung cấp mật khẩu, cookie, khóa riêng, bản xuất phân tích đầy đủ hoặc dữ liệu nhạy cảm. Đầu ra tách biệt quy tắc, lỗi chặn, lời khuyên, điều chưa biết, giới hạn bằng chứng, hành động, lớp xác minh, trạng thái sản xuất và kết quả bên ngoài đang chờ.

Skill từ chối thao túng thứ hạng, kinh nghiệm hoặc bằng chứng giả, trang doorway, nội dung hàng loạt không có giá trị, vượt kiểm soát truy cập, lộ dữ liệu và chứng nhận giả. Trang hoặc công cụ không truy cập được vẫn là chưa biết, không phải đã đạt.

Mỗi trang có thể lập chỉ mục phải giải quyết nhiệm vụ mà URL hiện có tốt nhất không đáp ứng. Dịch máy và kiểm tra cấu trúc không chứng minh chất lượng ngôn ngữ; mỗi phiên bản công khai cần được rà soát về sự thật và ngôn ngữ.

## Cài đặt

Cài từ chợ Skill được hỗ trợ hoặc sao chép toàn bộ thư mục `seo-delivery-guard` vào thư mục Skill mà tác nhân AI nhận diện. Tải lại Skill hoặc mở phiên mới rồi gọi:

```text
$seo-delivery-guard
```

Gói công khai chỉ chứa hướng dẫn văn bản và metadata; không có tệp thực thi, crawler, khóa API hay thành phần riêng cho hệ điều hành.

## Giới hạn Google Search

Kết luận về Google Search phải dựa trên tài liệu chính thức hiện hành hoặc dữ liệu bên thứ nhất đã xác minh. Công cụ bên thứ ba có thể cung cấp tín hiệu nhưng không xác định quyết định lập chỉ mục, yếu tố xếp hạng, rich results hay tính năng AI của Google.

SEO Delivery Guard là dự án mã nguồn mở độc lập, không liên kết, được chứng nhận, tài trợ hay xác nhận bởi Google.

## Nhà phát hành

- Nhà phát hành và trang chính thức: [once-email.com](https://once-email.com)
- Người tạo: helen.jar
- GitHub: [pangxin12345](https://github.com/pangxin12345)
- Hỗ trợ công khai: [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com)

Giấy phép MIT · Phiên bản 0.1.0

Xem thay đổi tại [CHANGELOG.md](../CHANGELOG.md).
