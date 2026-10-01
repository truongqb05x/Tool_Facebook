using System.Windows;

namespace FPlusClone.Views
{
    public partial class SpamGroupSettingsWindow : Window
    {
        public SpamGroupSettingsWindow()
        {
            InitializeComponent();
        }

        private void Close_Click(object sender, RoutedEventArgs e)
        {
            this.Close();
        }
    }
}
