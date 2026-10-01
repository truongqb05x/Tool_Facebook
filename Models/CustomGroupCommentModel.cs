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

        public event PropertyChangedEventHandler PropertyChanged;
        protected void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}
