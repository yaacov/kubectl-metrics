package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/yaacov/kubectl-metrics/pkg/version"
)

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Print the version information",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Printf("kubectl-metrics %s (commit: %s, built: %s)\n",
			version.Version, version.GitCommit, version.BuildDate)
	},
}

func init() {
	rootCmd.AddCommand(versionCmd)
}
