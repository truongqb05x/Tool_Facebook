using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace FPlusClone.Models
{
    public class CustomGroupCommentModel : INotifyPropertyChanged
    {
        private string _groupId;
        public string GroupId { get => _groupId; set { _groupId = value; OnPropertyChanged(); } }

        private string _content;
        public string Content { get => _content; set { _content = value; OnPropertyChanged(); } }

        // "Text" hoặc "Image"
        private string _commentType = "Text";
        public string CommentType { get => _commentType; set { _commentType = value; OnPropertyChanged(); OnPropertyChanged(nameof(TypeLabel)); } }

        // Đường dẫn ảnh (chỉ dùng khi CommentType == "Image")
        private string _imagePath;
        public string ImagePath { get => _imagePath; set { _imagePath = value; OnPropertyChanged(); } }

        public string TypeLabel => CommentType == "Image" ? "Ảnh" : "Text";

        public event PropertyChangedEventHandler PropertyChanged;
        protected void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}
