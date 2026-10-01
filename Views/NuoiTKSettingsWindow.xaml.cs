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

        private void Close_Click(object sender, RoutedEventArgs e)
        {
            this.Close();
        }
    }
}
