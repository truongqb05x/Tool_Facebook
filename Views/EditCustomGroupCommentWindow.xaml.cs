using System.Windows;

namespace FPlusClone.Views
{
    public partial class EditCustomGroupCommentWindow : Window
    {
        public string GroupId { get; private set; }
        public string CommentContent { get; private set; }

        public EditCustomGroupCommentWindow(string groupId = "", string content = "")
        {
            InitializeComponent();
            txtGroupId.Text = groupId;
            txtContent.Text = content;
        }

        private void Save_Click(object sender, RoutedEventArgs e)
        {
            GroupId = txtGroupId.Text.Trim();
            CommentContent = txtContent.Text;

            if (string.IsNullOrWhiteSpace(GroupId))
            {
                MessageBox.Show("Vui lòng nhập Group ID.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            DialogResult = true;
            Close();
        }

        private void Cancel_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }
    }
}
