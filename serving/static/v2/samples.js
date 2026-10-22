/* Mẫu do nhóm biên soạn, không lấy từ train/val/test.
   Chỉ dùng làm input demo cho giao diện serving; không dùng để huấn luyện/đánh giá. */
window.SENTIMENTX_SAMPLES = {
  positive: [
    "Màu đỏ gạch lên môi khá tươi, không bị xỉn dù mình không trang điểm nền. Thỏi son nhẹ, dễ tán và không làm khô môi suốt buổi sáng. Mình còn thích cách son phai đều sau khi ăn, không để lại viền khó coi.",
    "Chất son mềm như kem, tán một lớp là đủ che rãnh môi. Giá dễ chịu, shop còn bọc thêm xốp nên hộp đến tay nguyên vẹn.",
    "Mùi vanilla thoang thoảng, mình ngửi không thấy gắt. Đóng gói gọn gàng, vận chuyển nhanh hơn dự kiến.",
    "Màu cam đào hợp da ngăm, lên môi trong trẻo. Son bám ổn, ăn uống nhẹ vẫn còn lớp màu.",
    "Son mịn, màu chuẩn, giá ổn và giao nhanh.",
    "Mình thích phần vỏ kim loại chắc tay, nắp đóng nghe cạch một tiếng rõ. Ruột son xoay êm, không bị lỏng như vài cây trước đây. Shop còn bọc thêm lớp xốp nên thỏi son tới tay sạch sẽ, không một vết xước.",
    "Một lớp đã che được thâm môi, lớp hai thì màu đậm hơn hẳn. Giá dễ chịu so với lượng son, dùng cả năm chưa chắc hết.",
    "Hộp carton dày, có niêm phong và giấy chống sốc. Mở ra thỏi son còn nguyên, không trầy xước.",
    "Mùi trà xanh nhẹ, khác với các dòng son ngọt mình từng dùng. Chất son ráo, lên môi lì nhưng không kéo da.",
    "Son lên màu đều, không loang ở khóe môi. Shop gửi kèm một miếng test giấy, khá chu đáo."
  ],
  negative: [
    "Màu trên hình là hồng san hô mà nhận về lại ngả cam, mình khá thất vọng. Chất son lại bột và bám vào môi khô.",
    "Thỏi son có mùi nhựa, ngửi lâu thấy khó chịu. Mình đã thử tán mỏng nhưng vẫn bị vón ở khóe môi.",
    "Giao chậm, hộp móp và son bị xước.",
    "Shop gói hàng qua loa, chỉ một lớp nilon nên hộp bẹp góc. Son bên trong vẫn dùng được nhưng cảm giác không đáng tiền. Mình đã nhắn phản hồi mà shop chỉ trả lời cho có, không đưa ra cách giải quyết nào.",
    "Giá này mà độ bám kém quá, uống nước đã trôi gần hết. Mình phải dặm lại liên tục nên rất bất tiện.",
    "Mùi son hắc, kiểu mùi hóa học, mình không dám dùng gần em bé. Đành trả lại vì không hợp.",
    "Chất son lỏng quá, tán ra thì loang xuống cằm. Màu lên không đều, chỗ đậm chỗ nhạt.",
    "Nhận hàng sau gần hai tuần, trong khi shop ghi hai ngày. Hộp thì bị bóp méo, may son chưa gãy.",
    "Mình mua vì thấy quảng cáo lì lâu, nhưng thực tế ăn sáng xong là mất màu. Đắt so với trải nghiệm.",
    "Đầu son bị lệch, xoay lên thấy cạ vào thành nắp. Màu cũng không giống ảnh shop chụp, hơi ngả nâu. Đổi trả thì phải tự trả phí ship, mất gần tuần mới xong nên mình thôi."
  ],
  mixed: [
    "Màu son khá xinh và lên chuẩn, nhưng công thức son hơi khô nên môi mình bong nhẹ. Giá ổn, giao cũng nhanh.",
    "Hộp được gói chắc chắn và mùi hương khá dịu, tiếc là độ bám không được lâu. Uống trà sữa xong là phải dặm lại, mà mình lại lười mang son theo. Được cái màu lên tự nhiên nên vẫn tạm hài lòng.",
    "Chất son mịn, tán dễ, màu đẹp trong nắng. Điểm trừ là hộp bị móp một góc do vận chuyển.",
    "Son lên lì đẹp nhưng hơi bột, môi mình cần thoa son dưỡng trước. Shop giao đúng hẹn và đóng gói chắc.",
    "Giá phải chăng, màu cũng tươi, nhưng mùi hơi nồng với người nhạy cảm. Mình vẫn dùng được vì bám khá lâu.",
    "Mình thích cách son không dính ly, lại còn nhẹ môi. Nhưng đầu son hơi nhỏ nên tán mất thời gian.",
    "Đóng gói xinh, có thiệp cảm ơn, giao nhanh. Chất son thì hơi cứng, phải làm ấm môi mới lên màu đều.",
    "Màu đẹp và bền qua bữa trưa, nhưng giá cao hơn mặt bằng chung. Shop đóng gói kỹ nên mình vẫn thấy ổn.",
    "Mùi trái cây thoang thoảng, texture mướt, tán rất nhanh. Có điều phần nắp bấm không chặt, để trong túi cứ sợ bật ra. Mình vẫn giữ lại dùng ở nhà, còn lúc ra ngoài thì chọn cây khác.",
    "Giao hàng nhanh, hộp nguyên vẹn, màu đúng mô tả. Chỉ là son hơi trôi khi ăn đồ dầu, cần dặm lại."
  ]
};