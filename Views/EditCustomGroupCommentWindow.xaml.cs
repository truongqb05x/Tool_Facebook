using System.Windows;

namespace FPlusClone.Views
{
    public partial class EditCustomGroupCommentWindow : Window
    {
        public string GroupId { get; private set; }
        public string CommentContent { get; private set; }
        public string CommentType { get; private set; } = "Text"; // "Text" hoặc "Image"
        public string ImagePath { get; private set; }

        public EditCustomGroupCommentWindow(string groupId = "", string content = "", string commentType = "Text", string imagePath = "")
        {
            InitializeComponent();
            txtGroupId.Text = groupId;

            if (commentType == "Image")
            {
                rbImage.IsChecked = true;
                txtImagePath.Text = imagePath;
                txtImageCaption.Text = content;
                ShowImagePanel();
            }
            else
            {
                rbText.IsChecked = true;
                txtContent.Text = content;
                ShowTextPanel();
            }
        }

        private void CommentType_Changed(object sender, RoutedEventArgs e)
        {
            if (rbImage != null && rbImage.IsChecked == true)
                ShowImagePanel();
            else
                ShowTextPanel();
        }

        private void ShowTextPanel()
        {
            if (panelText != null) panelText.Visibility = Visibility.Visible;
            if (borderContent != null) borderContent.Visibility = Visibility.Visible;
            if (panelImage != null) panelImage.Visibility = Visibility.Collapsed;
        }

        private void ShowImagePanel()
        {
            if (panelText != null) panelText.Visibility = Visibility.Collapsed;
            if (borderContent != null) borderContent.Visibility = Visibility.Collapsed;
            if (panelImage != null) panelImage.Visibility = Visibility.Visible;
        }

        private void BrowseImage_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new Microsoft.Win32.OpenFileDialog
            {
                Title = "Chọn ảnh đính kèm",
                Filter = "Image files|*.jpg;*.jpeg;*.png;*.gif;*.bmp;*.webp|All files|*.*"
            };
            if (dialog.ShowDialog() == true)
            {
                txtImagePath.Text = dialog.FileName;
            }
        }

        private void Save_Click(object sender, RoutedEventArgs e)
        {
            GroupId = txtGroupId.Text.Trim();

            if (string.IsNullOrWhiteSpace(GroupId))
            {
                MessageBox.Show("Vui lòng nhập Group ID.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            if (rbImage.IsChecked == true)
            {
                CommentType = "Image";
                ImagePath = txtImagePath.Text.Trim();
                CommentContent = txtImageCaption.Text;

                if (string.IsNullOrWhiteSpace(ImagePath))
                {
                    MessageBox.Show("Vui lòng chọn ảnh đính kèm.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }
            }
            else
            {
                CommentType = "Text";
                ImagePath = string.Empty;
                CommentContent = txtContent.Text;

                if (string.IsNullOrWhiteSpace(CommentContent))
                {
                    MessageBox.Show("Vui lòng nhập nội dung comment.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }
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
