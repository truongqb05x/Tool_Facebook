using System.Windows;

namespace FPlusClone.Views
{
    public partial class NuoiTKSettingsWindow : Window
    {
        public NuoiTKSettingsWindow()
        {
            InitializeComponent();
        }

        private void BtnPostSettings_Click(object sender, RoutedEventArgs e)
        {
            var settingsWindow = new PostSettingsWindow();
            settingsWindow.ShowDialog();
        }
        
        private void BtnBrowseStoryFolder_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new Microsoft.Win32.OpenFolderDialog();
            dialog.Title = "Chọn thư mục chứa ảnh để đăng Story";
            if (dialog.ShowDialog() == true)
            {
                if (this.DataContext is FPlusClone.ViewModels.TabNuoiTKViewModel vm)
                {
                    vm.StoryFolderPath = dialog.FolderName;
                }
            }
        }

        private void Close_Click(object sender, RoutedEventArgs e)
        {
            this.Close();
        }
    }
}
